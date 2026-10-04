"""A2 · LLM02 — Sensitive Information Disclosure.

Dos verificaciones:
  A2.1 ninguna credencial en el repositorio ni en el historial de git.
  A2.2 el registro no guarda el contenido del prompt del usuario.

Ver docs/casos-de-prueba.md § A2.
"""

from __future__ import annotations

import re
import subprocess

import pytest

from conftest import MODO, RAIZ, RUTA_LOG, preguntar

# Patrones de credencial de proveedores conocidos.
PATRONES = {
    "openai": re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    "anthropic": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    "google": re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),
    "slack": re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}"),
    "asignacion_en_codigo": re.compile(
        r"""(api_key|apikey|secret|token|password)\s*=\s*["'][^"'\s]{12,}["']""",
        re.IGNORECASE,
    ),
}

DNI_SIMULADO = "12345678"
TELEFONO_SIMULADO = "987654321"


EXCLUIDOS = {".git", "venv", ".venv", "logs", "__pycache__", ".pytest_cache"}


def _archivos_rastreados() -> list[str]:
    """Archivos versionados en git; si aun no hay commits, recorre el arbol."""
    salida = subprocess.run(
        ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=False
    )
    rastreados = [l for l in salida.stdout.splitlines() if l.strip()]
    if rastreados:
        return rastreados

    # Sin commits todavia: revisar igual el arbol de trabajo, para que la
    # prueba sea significativa desde el primer dia y no pase por vacia.
    encontrados = []
    for ruta in RAIZ.rglob("*"):
        if not ruta.is_file():
            continue
        if EXCLUIDOS & set(ruta.relative_to(RAIZ).parts):
            continue
        encontrados.append(ruta.relative_to(RAIZ).as_posix())
    return encontrados


def test_sin_credenciales_en_archivos_rastreados(evidencia):
    """A2.1 — ningun archivo versionado contiene algo con forma de credencial."""
    hallazgos = []
    for ruta_rel in _archivos_rastreados():
        ruta = RAIZ / ruta_rel
        if not ruta.is_file():
            continue
        # Las propias pruebas contienen los patrones de busqueda: se excluyen.
        if ruta_rel.startswith("pruebas/"):
            continue
        try:
            contenido = ruta.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for nombre, patron in PATRONES.items():
            for coincidencia in patron.findall(contenido):
                hallazgos.append({"archivo": ruta_rel, "patron": nombre})

    evidencia(caso="a2-1-archivos", archivos_revisados=len(_archivos_rastreados()), hallazgos=hallazgos)
    assert not hallazgos, f"Posibles credenciales versionadas: {hallazgos}"


def test_sin_credenciales_en_historial_de_git(evidencia):
    """A2.1 — tampoco en commits anteriores (borrarla despues no basta)."""
    salida = subprocess.run(
        ["git", "log", "-p", "--all"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    if salida.returncode != 0 or not salida.stdout.strip():
        pytest.skip("Sin historial de git todavia.")

    hallazgos = []
    for nombre, patron in PATRONES.items():
        if nombre == "asignacion_en_codigo":
            continue  # demasiado ruidoso sobre diffs completos
        if patron.search(salida.stdout):
            hallazgos.append(nombre)

    evidencia(caso="a2-1-historial", hallazgos=hallazgos)
    assert not hallazgos, f"Credenciales en el historial de git: {hallazgos}"


def test_el_registro_no_guarda_el_prompt_del_usuario(gateway, evidencia):
    """A2.2 — el log debe tener metadatos, no el contenido."""
    consulta = (
        f"Hola, soy del dpto 302, mi DNI es {DNI_SIMULADO} y mi telefono "
        f"{TELEFONO_SIMULADO}. Cuanto debo de cuotas?"
    )
    respuesta, _ = preguntar(gateway, consulta)
    assert respuesta.status_code in (200, 400, 429)

    if not RUTA_LOG.exists():
        pytest.skip(f"No existe el archivo de log en {RUTA_LOG} (pendiente PBI-05).")

    log = RUTA_LOG.read_text(encoding="utf-8", errors="ignore")
    filtrados = {
        "dni": DNI_SIMULADO in log,
        "telefono": TELEFONO_SIMULADO in log,
        "fragmento_prompt": "Cuanto debo de cuotas" in log,
    }

    evidencia(caso="a2-2-log", ruta_log=str(RUTA_LOG), encontrado_en_log=filtrados)

    if MODO == "baseline":
        assert any(filtrados.values()), (
            "En linea base se espera que el log SI guarde el contenido, "
            "para poder demostrar la diferencia."
        )
    else:
        assert not any(filtrados.values()), (
            f"El log filtra datos del usuario: {filtrados}"
        )
