"""Cliente del proveedor de inferencia (Ollama local).

Es el único módulo que habla con el proveedor. Ninguna otra parte del sistema
debe llamarlo directamente: ese es el sentido de un gateway.
"""

from __future__ import annotations

import httpx

import config


class ErrorProveedor(Exception):
    """Fallo al hablar con el proveedor upstream."""


async def disponible() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as cliente:
            respuesta = await cliente.get(f"{config.OLLAMA_URL}/api/tags")
            return respuesta.status_code == 200
    except Exception:
        return False


async def completar(mensaje_usuario: str, max_tokens: int) -> dict:
    """Envía la consulta al modelo y devuelve texto y uso de tokens."""
    cuerpo = {
        "model": config.OLLAMA_MODELO,
        "messages": [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": mensaje_usuario},
        ],
        "stream": False,
        "options": {"num_predict": max_tokens},
    }

    try:
        async with httpx.AsyncClient(timeout=config.TIMEOUT_PROVEEDOR) as cliente:
            respuesta = await cliente.post(f"{config.OLLAMA_URL}/api/chat", json=cuerpo)
            respuesta.raise_for_status()
            datos = respuesta.json()
    except Exception as e:
        raise ErrorProveedor(str(e)) from e

    return {
        "texto": datos.get("message", {}).get("content", ""),
        "tokens_entrada": datos.get("prompt_eval_count", 0),
        "tokens_salida": datos.get("eval_count", 0),
    }
