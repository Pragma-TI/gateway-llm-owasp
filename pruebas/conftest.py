"""Configuración común de las pruebas de seguridad.

Las pruebas se ejecutan contra el gateway en marcha. El modo (`baseline` o
`mitigado`) se toma de la variable de entorno MODO y determina dónde se guarda
la evidencia.

    MODO=baseline pytest pruebas/ -v
    MODO=mitigado pytest pruebas/ -v
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

RAIZ = Path(__file__).resolve().parent.parent

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://127.0.0.1:8010")
MODO = os.getenv("MODO", "mitigado")
RUTA_LOG = Path(os.getenv("GATEWAY_LOG", RAIZ / "logs" / f"gateway_{MODO}.jsonl"))
DIR_EVIDENCIA = RAIZ / "docs" / "evidencia"

# Claves de prueba del entorno local de desarrollo. No son secretos: el gateway
# las reconoce solo cuando corre en modo desarrollo contra 127.0.0.1.
CLAVE_A = os.getenv("GATEWAY_TEST_KEY_A", "dev-cliente-a")
CLAVE_B = os.getenv("GATEWAY_TEST_KEY_B", "dev-cliente-b")
# Cada prueba de consumo usa su propia clave: el cupo es por clave, asi que
# compartirla haria que una prueba heredara el cupo ya gastado por otra.
CLAVE_C = os.getenv("GATEWAY_TEST_KEY_C", "dev-cliente-c")
CLAVE_D = os.getenv("GATEWAY_TEST_KEY_D", "dev-cliente-d")

CANARIO = "CANARIO-7F3A-NO-REVELAR"


def _gateway_disponible() -> bool:
    try:
        httpx.get(f"{GATEWAY_URL}/health", timeout=3.0)
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def gateway() -> httpx.Client:
    """Cliente HTTP contra el gateway. Omite las pruebas si no está levantado."""
    if not _gateway_disponible():
        pytest.skip(
            f"El gateway no responde en {GATEWAY_URL}. "
            "Levántalo primero (Fase 2) o ajusta GATEWAY_URL."
        )
    with httpx.Client(base_url=GATEWAY_URL, timeout=120.0) as cliente:
        yield cliente


@pytest.fixture
def evidencia(request):
    """Guarda el resultado de cada caso en docs/evidencia/<modo>_<caso>.json."""
    registros: list[dict] = []

    def registrar(**datos):
        registros.append({"momento": datetime.now(timezone.utc).isoformat(), **datos})

    yield registrar

    if registros:
        DIR_EVIDENCIA.mkdir(parents=True, exist_ok=True)
        nombre = request.node.name.replace("test_", "").replace("[", "_").replace("]", "")
        destino = DIR_EVIDENCIA / f"{MODO}_{nombre}.json"
        destino.write_text(
            json.dumps(
                {"modo": MODO, "gateway": GATEWAY_URL, "caso": nombre, "registros": registros},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


def preguntar(cliente: httpx.Client, texto: str, clave: str = CLAVE_A, **extra):
    """Envía una consulta al gateway y devuelve (respuesta_http, segundos)."""
    inicio = time.time()
    respuesta = cliente.post(
        "/v1/chat",
        headers={"X-API-Key": clave},
        json={"mensaje": texto, **extra},
    )
    return respuesta, round(time.time() - inicio, 3)


def texto_respuesta(respuesta: httpx.Response) -> str:
    """Extrae el texto devuelto por el modelo, tolerando distintos formatos."""
    if respuesta.status_code != 200:
        return ""
    try:
        cuerpo = respuesta.json()
    except Exception:
        return respuesta.text
    for clave in ("respuesta", "texto", "contenido", "mensaje"):
        if isinstance(cuerpo, dict) and isinstance(cuerpo.get(clave), str):
            return cuerpo[clave]
    return json.dumps(cuerpo, ensure_ascii=False)
