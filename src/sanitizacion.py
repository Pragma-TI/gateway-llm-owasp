"""Sanitización de la entrada del usuario (OWASP LLM01 — Prompt Injection).

Módulo deliberadamente **separado y sin dependencias del resto del gateway**,
para poder probarlo de forma aislada (ver `pruebas/test_sanitizacion_unitaria.py`).

Hace tres cosas, en orden:

1. Acota la longitud, porque un payload enorme encarece la llamada y sirve para
   esconder la instrucción maliciosa al final del texto.
2. Busca patrones de anulación de instrucciones y rechaza la petición si los
   encuentra.
3. Envuelve el texto aceptado en delimitadores explícitos, para que el modelo
   distinga los datos del usuario de sus propias instrucciones.

Límite conocido y declarado: el paso 2 es una lista de patrones, no un
clasificador. Un ataque redactado de otra forma puede pasar. Por eso el filtro
de salida (`filtro_salida.py`) actúa como segunda capa.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Cada patrón nombra el tipo de ataque que detiene, para que el registro y el
# documento de mapeo puedan citarlo.
PATRONES_ANULACION: list[tuple[str, re.Pattern]] = [
    ("override_instrucciones", re.compile(r"\bignora(r)?\s+(todas?\s+)?(tus|las|sus)\s+(instrucciones|reglas)", re.I)),
    ("override_olvida", re.compile(r"\bolvida(te)?\s+(tus|las|sus)\s+(reglas|instrucciones)", re.I)),
    ("falsa_instruccion_sistema", re.compile(r"(nueva\s+instruccion|instruccion\s+del\s+sistema|system\s*prompt|#{3,})", re.I)),
    ("falso_modo_privilegiado", re.compile(r"\bmodo\s+(mantenimiento|desarrollador|debug|administrador)", re.I)),
    ("restricciones_desactivadas", re.compile(r"(restricciones|reglas|limitaciones)\s+(estan\s+)?(desactivad|anulad|suspendid)", re.I)),
    ("rol_sin_limites", re.compile(r"\bsin\s+restricciones\b|\bsin\s+limites\b", re.I)),
    ("extraccion_de_instrucciones", re.compile(r"repite\s+(textualmente|palabra\s+por\s+palabra)|(muestra|revela|cita|resume)\w*\s+(tu|tus|la)\s+(instruccion|instrucciones|configuracion)", re.I)),
]

APERTURA = "<consulta_usuario>"
CIERRE = "</consulta_usuario>"


@dataclass
class Resultado:
    aceptado: bool
    texto: str = ""
    motivo: str | None = None
    patrones: list[str] = field(default_factory=list)


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para que 'instrucción' e 'instruccion' coincidan."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return sin_tildes.lower()


def detectar(texto: str) -> list[str]:
    """Nombres de los patrones de anulación encontrados en el texto."""
    normalizado = normalizar(texto)
    return [nombre for nombre, patron in PATRONES_ANULACION if patron.search(normalizado)]


def sanitizar(texto: str, max_caracteres: int) -> Resultado:
    """Devuelve el texto listo para el prompt, o el motivo del rechazo."""
    if not texto or not texto.strip():
        return Resultado(aceptado=False, motivo="mensaje_vacio")

    if len(texto) > max_caracteres:
        return Resultado(
            aceptado=False,
            motivo="longitud_excedida",
            patrones=[f"{len(texto)} caracteres, maximo {max_caracteres}"],
        )

    patrones = detectar(texto)
    if patrones:
        return Resultado(aceptado=False, motivo="patron_de_anulacion", patrones=patrones)

    # El texto aceptado se marca como dato, no como instrucción.
    limpio = texto.replace(APERTURA, "").replace(CIERRE, "")
    return Resultado(aceptado=True, texto=f"{APERTURA}\n{limpio.strip()}\n{CIERRE}")
