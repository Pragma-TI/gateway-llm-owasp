"""Gateway LLM — punto de entrada único hacia el proveedor de inferencia.

Fase 2 del proyecto: el gateway funciona, pero las mitigaciones aún NO están
implementadas. Este es el estado que produce la línea base contra la que se
comparan las protecciones de la Fase 3.

Arranque:
    uvicorn main:app --app-dir src --port 8010                 (mitigado, por defecto)
    GATEWAY_MODO=baseline uvicorn main:app --app-dir src ...   (sin protecciones)
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

import config
import proveedor
import registro

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("gateway")

app = FastAPI(
    title="Gateway LLM con Seguridad OWASP",
    description="Punto de entrada único hacia el proveedor de inferencia.",
    version="0.2.0-fase2",
)


@app.on_event("startup")
async def avisar_modo() -> None:
    if config.ES_BASELINE:
        log.warning(
            "GATEWAY_MODO=baseline — TODAS las mitigaciones estan APAGADAS. "
            "Este modo existe unicamente para grabar la linea base del proyecto."
        )
    else:
        log.info("Modo mitigado. Mitigaciones activas se implementan en la Fase 3.")


class Consulta(BaseModel):
    mensaje: str = Field(..., description="Texto enviado por el usuario final")
    max_tokens: int = Field(default=300, ge=1)


def identificar_cliente(api_key: str | None) -> str:
    """Autentica a la aplicación cliente por su API key."""
    if not api_key or api_key not in config.CLIENTES:
        raise HTTPException(status_code=401, detail="API key ausente o no reconocida.")
    return config.CLIENTES[api_key]


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
async def chat(consulta: Consulta, x_api_key: str | None = Header(default=None)) -> dict:
    inicio = time.time()
    cliente = identificar_cliente(x_api_key)

    # --- Fase 3 insertará aquí: sanitización (LLM01) y techo de tokens (LLM10) ---
    mensaje = consulta.mensaje
    max_tokens = consulta.max_tokens

    try:
        resultado = await proveedor.completar(mensaje, max_tokens)
    except proveedor.ErrorProveedor as e:
        latencia_ms = int((time.time() - inicio) * 1000)
        registro.registrar(
            endpoint="/v1/chat",
            cliente=cliente,
            resultado="error_proveedor",
            latencia_ms=latencia_ms,
        )
        if config.MITIGAR_ERRORES:
            raise HTTPException(
                status_code=503,
                detail="El servicio de IA no esta disponible. Intenta nuevamente en unos minutos.",
            ) from e
        # Línea base: se expone el error interno tal cual (comportamiento a corregir).
        raise HTTPException(status_code=500, detail=f"Fallo upstream: {e}") from e

    # --- Fase 3 insertará aquí: filtro de salida (LLM07) ---
    texto = resultado["texto"]
    latencia_ms = int((time.time() - inicio) * 1000)

    registro.registrar(
        endpoint="/v1/chat",
        cliente=cliente,
        resultado="ok",
        latencia_ms=latencia_ms,
        tokens_entrada=resultado["tokens_entrada"],
        tokens_salida=resultado["tokens_salida"],
        max_tokens_aplicado=max_tokens,
        prompt_usuario=consulta.mensaje,
        respuesta_modelo=texto,
    )

    return {
        "respuesta": texto,
        "modelo": config.OLLAMA_MODELO,
        "latencia_ms": latencia_ms,
        "max_tokens_aplicado": max_tokens,
        "tokens": {
            "entrada": resultado["tokens_entrada"],
            "salida": resultado["tokens_salida"],
        },
    }
