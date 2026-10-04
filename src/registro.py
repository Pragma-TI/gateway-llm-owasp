"""Registro de auditoría del gateway (OWASP LLM02).

Escribe una línea JSON por petición en `logs/gateway.jsonl`.

Con la mitigación activa se registran **metadatos**: qué pasó, cuándo, cuánto
tardó y en qué terminó. Nunca el contenido del prompt del usuario ni la
respuesta del modelo, porque un log que guarda todo "por si sirve para depurar"
se convierte él mismo en la fuga que LLM02 advierte.

Con MITIGAR_REGISTRO apagado se registra todo, para poder demostrar la
diferencia en la línea base.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone

import config

_candado = threading.Lock()

# Contadores en memoria para la métrica agregada de violaciones
# (Guardrail Violation Rate, del documento Agent Performance KPIs).
_totales = {"peticiones": 0, "violaciones": 0}

CAMPOS_SENSIBLES = ("prompt_usuario", "respuesta_modelo")


def registrar(**evento) -> None:
    """Añade un evento al log, filtrando campos sensibles si corresponde."""
    _totales["peticiones"] += 1
    if evento.get("violacion"):
        _totales["violaciones"] += 1

    linea = {"timestamp": datetime.now(timezone.utc).isoformat(), **evento}

    if config.MITIGAR_REGISTRO:
        for campo in CAMPOS_SENSIBLES:
            linea.pop(campo, None)
        linea["contenido_omitido"] = True

    config.RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _candado:
        with config.RUTA_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(linea, ensure_ascii=False) + "\n")


def metricas() -> dict:
    """Métricas agregadas desde que arrancó el proceso."""
    total = _totales["peticiones"]
    violaciones = _totales["violaciones"]
    tasa = round(violaciones / total * 100, 2) if total else 0.0
    return {
        "peticiones": total,
        "violaciones": violaciones,
        "guardrail_violation_rate_pct": tasa,
    }
