"""Degradación controlada ante fallos del proveedor (requisito no funcional).

El documento del proyecto lo pide explícitamente: "el sistema debe degradarse de
forma controlada (mensajes de error claros) ante fallos del proveedor upstream,
no exponer trazas de error internas al cliente".

La caída del proveedor se simula apuntando el gateway a un puerto donde no hay
nadie escuchando. No hace falta apagar Ollama ni tener red: la prueba es
reproducible en cualquier máquina.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import config  # noqa: E402
import main  # noqa: E402

PUERTO_MUERTO = "http://127.0.0.1:19999"
CLAVE = "dev-cliente-a"


def _pedir(monkeypatch, mitigar_errores: bool):
    monkeypatch.setattr(config, "OLLAMA_URL", PUERTO_MUERTO)
    monkeypatch.setattr(config, "MITIGAR_ERRORES", mitigar_errores)
    with TestClient(main.app, raise_server_exceptions=False) as cliente:
        return cliente.post(
            "/v1/chat",
            headers={"X-API-Key": CLAVE},
            json={"mensaje": "Hola, cuando se pagan las cuotas?", "max_tokens": 20},
        )


def test_con_mitigacion_el_cliente_recibe_un_mensaje_claro(monkeypatch, evidencia):
    respuesta = _pedir(monkeypatch, mitigar_errores=True)
    detalle = respuesta.json().get("detail", "")

    evidencia(
        caso="degradacion-mitigada",
        status=respuesta.status_code,
        detalle=detalle,
        filtra_url_interna=PUERTO_MUERTO in respuesta.text,
        filtra_traza=any(p in respuesta.text for p in ("Traceback", "File \"", ".py\", line")),
    )

    assert respuesta.status_code == 503
    assert "no esta disponible" in detalle.lower()
    # Lo importante: el cliente no ve las tripas del sistema.
    assert PUERTO_MUERTO not in respuesta.text, "Se filtro la URL interna del proveedor."
    assert "Traceback" not in respuesta.text, "Se filtro una traza de error."


def test_sin_mitigacion_se_filtra_el_error_interno(monkeypatch, evidencia):
    """Línea base: el comportamiento que la mitigación corrige.

    El cliente recibe HTTP 500 con el texto de la excepción del proveedor
    ("Fallo upstream: All connection attempts failed") en lugar de un mensaje
    pensado para él. Es información del funcionamiento interno que un atacante
    puede usar para mapear el sistema.
    """
    respuesta = _pedir(monkeypatch, mitigar_errores=False)
    detalle = respuesta.json().get("detail", "")

    evidencia(
        caso="degradacion-baseline",
        status=respuesta.status_code,
        detalle=detalle[:300],
        expone_excepcion_interna="upstream" in detalle.lower(),
    )

    assert respuesta.status_code == 500
    assert "upstream" in detalle.lower(), (
        "Sin la mitigacion se espera que el error interno llegue al cliente: "
        f"ese es el punto de comparacion. Recibido: {detalle!r}"
    )
    assert "intenta nuevamente" not in detalle.lower(), (
        "En linea base no deberia haber mensaje amable para el usuario."
    )
