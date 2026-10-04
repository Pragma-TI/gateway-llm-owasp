"""Filtro de la salida del modelo (OWASP LLM07 — System Prompt Leakage).

Segunda capa de defensa: aunque un ataque consiga esquivar la sanitización de
entrada, la respuesta se revisa antes de devolverla al cliente.

La detección es **binaria**, no heurística: el system prompt contiene un canario
único (`CANARIO-7F3A-NO-REVELAR`). Si esa cadena aparece en la respuesta, hubo
fuga, sin lugar a interpretación. Como refuerzo se busca también una frase
distintiva del system prompt, por si el modelo lo parafrasea omitiendo el canario.
"""

from __future__ import annotations

import re

import config

MENSAJE_SEGURO = (
    "No puedo compartir mi configuracion interna. "
    "Puedo ayudarte con el reglamento, las cuotas o reportar una incidencia."
)

# Frase distintiva del system prompt, para detectar copias parafraseadas.
FRAGMENTO_DISTINTIVO = "asistente virtual de un edificio residencial"


def _sin_separadores(texto: str) -> str:
    """Quita guiones y espacios: evita que 'CANARIO 7F3A' burle la comparacion."""
    return re.sub(r"[\s\-_]", "", texto).upper()


def revisar(respuesta: str) -> tuple[bool, str, str | None]:
    """Devuelve (hubo_fuga, texto_a_devolver, motivo)."""
    if not respuesta:
        return False, respuesta, None

    canario_plano = _sin_separadores(config.CANARIO)

    if config.CANARIO in respuesta or canario_plano in _sin_separadores(respuesta):
        return True, MENSAJE_SEGURO, "canario_en_respuesta"

    if FRAGMENTO_DISTINTIVO in respuesta.lower():
        return True, MENSAJE_SEGURO, "fragmento_system_prompt"

    return False, respuesta, None
