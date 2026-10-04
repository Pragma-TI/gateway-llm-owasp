"""A4 · LLM10 — Unbounded Consumption.

  A4.1 limite de peticiones por ventana de tiempo.
  A4.2 el limite es por API key, no por IP (las dos claves salen de la misma maquina).
  A4.3 techo de max_tokens.

Ver docs/casos-de-prueba.md § A4.
"""

from __future__ import annotations

import pytest

from conftest import CLAVE_A, CLAVE_B, MODO, preguntar

PETICIONES = 30
CONSULTA_CORTA = "Hola"


def _disparar(gateway, cantidad: int, clave: str) -> list[int]:
    codigos = []
    for _ in range(cantidad):
        respuesta, _ = preguntar(gateway, CONSULTA_CORTA, clave=clave, max_tokens=16)
        codigos.append(respuesta.status_code)
    return codigos


def test_limite_de_peticiones(gateway, evidencia):
    """A4.1 — sin proteccion pasan todas; con proteccion aparecen 429."""
    codigos = _disparar(gateway, PETICIONES, CLAVE_A)
    rechazadas = codigos.count(429)
    aceptadas = codigos.count(200)

    evidencia(
        caso="a4-1-rate-limit",
        peticiones=PETICIONES,
        aceptadas=aceptadas,
        rechazadas_429=rechazadas,
        primera_rechazada=(codigos.index(429) + 1) if 429 in codigos else None,
        secuencia=codigos,
    )

    if MODO == "baseline":
        assert rechazadas == 0, (
            "En linea base ninguna peticion deberia rechazarse: "
            f"hubo {rechazadas} respuestas 429."
        )
    else:
        assert rechazadas > 0, (
            f"Con el limite activo, {PETICIONES} peticiones seguidas deberian "
            "producir al menos un 429."
        )
        assert aceptadas > 0, "El limite no puede bloquear absolutamente todo."


def test_el_limite_es_por_api_key_y_no_por_ip(gateway, evidencia):
    """A4.2 — la clave B debe seguir funcionando aunque A este bloqueada.

    Ambas claves salen de la MISMA IP. Si el limite estuviera puesto por IP,
    B quedaria bloqueada sin haber consumido su cupo: ese es el error que el
    documento del curso advierte explicitamente.
    """
    if MODO == "baseline":
        pytest.skip("Sin limite activo no hay nada que distinguir.")

    codigos_a = _disparar(gateway, PETICIONES, CLAVE_A)
    assert 429 in codigos_a, "Primero hay que agotar el cupo de la clave A."

    respuesta_b, _ = preguntar(gateway, CONSULTA_CORTA, clave=CLAVE_B, max_tokens=16)

    evidencia(
        caso="a4-2-aislamiento-por-clave",
        clave_a_rechazadas=codigos_a.count(429),
        status_clave_b=respuesta_b.status_code,
    )

    assert respuesta_b.status_code != 429, (
        "La clave B fue bloqueada sin consumir su cupo: el limite esta puesto "
        "por IP y no por API key."
    )


def test_techo_de_max_tokens(gateway, evidencia):
    """A4.3 — una peticion con max_tokens absurdo no debe reenviarse tal cual."""
    respuesta, segundos = preguntar(
        gateway, "Escribe un ensayo largo sobre convivencia vecinal.", max_tokens=100000
    )

    cuerpo = {}
    try:
        cuerpo = respuesta.json()
    except Exception:
        pass

    evidencia(
        caso="a4-3-techo-tokens",
        max_tokens_solicitado=100000,
        status=respuesta.status_code,
        segundos=segundos,
        max_tokens_aplicado=cuerpo.get("max_tokens_aplicado"),
    )

    if MODO == "baseline":
        assert respuesta.status_code == 200
    else:
        aplicado = cuerpo.get("max_tokens_aplicado")
        assert respuesta.status_code == 400 or (aplicado is not None and aplicado < 100000), (
            "Con el techo activo la peticion debe rechazarse o recortarse, "
            f"y el gateway debe reportar el valor aplicado (recibido: {aplicado})."
        )
