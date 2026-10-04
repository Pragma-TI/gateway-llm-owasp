"""Gateway LLM — punto de entrada único hacia el proveedor de inferencia.

Cada mitigación vive en su propio módulo y se activa con un interruptor, para
que la demostración "sin protección / con protección" sea el mismo código con
una variable cambiada:

    uvicorn main:app --app-dir src --port 8010                 → mitigado (por defecto)
    GATEWAY_MODO=baseline uvicorn main:app --app-dir src ...   → sin protecciones

Mapeo a OWASP Top 10 for LLM Applications (2025):
    LLM01 Prompt Injection              → sanitizacion.py
    LLM02 Sensitive Info Disclosure     → registro.py + credenciales por entorno
    LLM07 System Prompt Leakage         → filtro_salida.py
    LLM10 Unbounded Consumption         → slowapi por API key + techo de max_tokens
"""

# NOTA: este modulo NO usa `from __future__ import annotations` a proposito.
# Con las anotaciones diferidas, FastAPI resuelve los tipos del endpoint en el
# modulo del decorador de slowapi (donde `Consulta` no existe) y termina
# tratando el cuerpo JSON como parametro de URL, devolviendo 422 en todo.
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import config
import filtro_salida
import proveedor
import registro
import sanitizacion

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("gateway")

@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    """Avisa en qué modo arrancó el gateway."""
    if config.ES_BASELINE:
        log.warning(
            "GATEWAY_MODO=baseline — TODAS las mitigaciones estan APAGADAS. "
            "Este modo existe unicamente para grabar la linea base del proyecto."
        )
    else:
        log.info("Modo mitigado: LLM01, LLM02, LLM07 y LLM10 activas.")
    yield


app = FastAPI(
    title="Gateway LLM con Seguridad OWASP",
    description="Punto de entrada único hacia el proveedor de inferencia.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


def clave_del_cliente(request: Request) -> str:
    """Identidad para el límite de consumo: la API key, no la IP.

    Un gateway recibe tráfico de varias aplicaciones que pueden compartir
    servidor. Limitar por IP las haría competir por el mismo cupo y bloquearse
    entre ellas.
    """
    return request.headers.get("x-api-key") or get_remote_address(request)


limiter = Limiter(key_func=clave_del_cliente)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Cuando la mitigación está apagada, el decorador no hace nada.
aplicar_limite = (
    limiter.limit(config.LIMITE_PETICIONES) if config.MITIGAR_LIMITE else (lambda f: f)
)


class Consulta(BaseModel):
    mensaje: str = Field(..., description="Texto enviado por el usuario final")
    max_tokens: int = Field(default=300, ge=1)


def identificar_cliente(api_key: str | None) -> str:
    if not api_key or api_key not in config.CLIENTES:
        raise HTTPException(status_code=401, detail="API key ausente o no reconocida.")
    return config.CLIENTES[api_key]


@app.get("/")
async def raiz() -> dict:
    """Punto de entrada informativo: qué es este servicio y qué se puede hacer."""
    return {
        "servicio": "Gateway LLM con Seguridad OWASP",
        "descripcion": "Punto de entrada unico entre las aplicaciones cliente y el proveedor de inferencia.",
        "modo": config.MODO,
        "documentacion_interactiva": "/docs",
        "endpoints": {
            "POST /v1/chat": "Consulta al modelo. Requiere la cabecera X-API-Key.",
            "GET /health": "Estado del gateway, del proveedor y de cada mitigacion.",
            "GET /metricas": "Peticiones, violaciones y Guardrail Violation Rate.",
        },
        "owasp_cubierto": {
            "LLM01": "Prompt Injection — sanitizacion de entrada",
            "LLM02": "Sensitive Information Disclosure — credenciales y registro",
            "LLM07": "System Prompt Leakage — filtro de salida",
            "LLM10": "Unbounded Consumption — limite por API key y techo de tokens",
        },
    }


@app.get("/health")
async def health() -> dict:
    return {
        "estado": "ok",
        "modo": config.MODO,
        "proveedor_disponible": await proveedor.disponible(),
        "modelo": config.OLLAMA_MODELO,
        "mitigaciones": {
            "LLM01_sanitizacion": config.MITIGAR_SANITIZACION,
            "LLM02_registro": config.MITIGAR_REGISTRO,
            "LLM07_fuga_prompt": config.MITIGAR_FUGA,
            "LLM10_limite": config.MITIGAR_LIMITE,
            "degradacion_controlada": config.MITIGAR_ERRORES,
        },
    }


@app.get("/metricas")
async def metricas() -> dict:
    return registro.metricas()


@app.post("/v1/chat")
@aplicar_limite
async def chat(
    request: Request,
    consulta: Consulta,
    x_api_key: str | None = Header(default=None),
) -> dict:
    inicio = time.time()
    cliente = identificar_cliente(x_api_key)

    def ms() -> int:
        return int((time.time() - inicio) * 1000)

    # --- LLM10: techo de tokens ---------------------------------------------
    max_tokens = consulta.max_tokens
    if config.MITIGAR_LIMITE:
        max_tokens = min(max_tokens, config.MAX_TOKENS_TECHO)

    # --- LLM01: sanitización de la entrada -----------------------------------
    if config.MITIGAR_SANITIZACION:
        revision = sanitizacion.sanitizar(consulta.mensaje, config.MAX_CARACTERES_PROMPT)
        if not revision.aceptado:
            registro.registrar(
                endpoint="/v1/chat",
                cliente=cliente,
                resultado="rechazado_sanitizacion",
                motivo=revision.motivo,
                patrones=revision.patrones,
                latencia_ms=ms(),
                violacion=True,
            )
            raise HTTPException(
                status_code=400,
                detail=f"Consulta rechazada por el control de entrada ({revision.motivo}).",
            )
        mensaje = revision.texto
    else:
        mensaje = consulta.mensaje

    # --- Llamada al proveedor ------------------------------------------------
    try:
        resultado = await proveedor.completar(mensaje, max_tokens)
    except proveedor.ErrorProveedor as e:
        registro.registrar(
            endpoint="/v1/chat",
            cliente=cliente,
            resultado="error_proveedor",
            latencia_ms=ms(),
        )
        if config.MITIGAR_ERRORES:
            raise HTTPException(
                status_code=503,
                detail="El servicio de IA no esta disponible. Intenta nuevamente en unos minutos.",
            ) from e
        raise HTTPException(status_code=500, detail=f"Fallo upstream: {e}") from e

    # --- LLM07: filtro de la salida ------------------------------------------
    texto = resultado["texto"]
    motivo_fuga = None
    if config.MITIGAR_FUGA:
        hubo_fuga, texto, motivo_fuga = filtro_salida.revisar(texto)
        if hubo_fuga:
            log.warning("Fuga de system prompt bloqueada (%s)", motivo_fuga)

    registro.registrar(
        endpoint="/v1/chat",
        cliente=cliente,
        resultado="bloqueado_fuga" if motivo_fuga else "ok",
        motivo=motivo_fuga,
        latencia_ms=ms(),
        tokens_entrada=resultado["tokens_entrada"],
        tokens_salida=resultado["tokens_salida"],
        max_tokens_aplicado=max_tokens,
        violacion=bool(motivo_fuga),
        prompt_usuario=consulta.mensaje,
        respuesta_modelo=resultado["texto"],
    )

    return {
        "respuesta": texto,
        "modelo": config.OLLAMA_MODELO,
        "latencia_ms": ms(),
        "max_tokens_aplicado": max_tokens,
        "tokens": {
            "entrada": resultado["tokens_entrada"],
            "salida": resultado["tokens_salida"],
        },
    }
