# ADR-002 — Categorías OWASP cubiertas y diseño del límite de consumo

- **Fecha:** 3 de octubre de 2026
- **Estado:** Aceptada

## Contexto

El documento del proyecto fija tres categorías obligatorias y deja una cuarta a elección
del estudiante. Además advierte explícitamente un error común de diseño: limitar el
consumo por dirección IP en vez de por usuario o API key.

## Decisiones

### 1. Las cuatro categorías

| Categoría | Origen | Mitigación |
|---|---|---|
| LLM01 — Prompt Injection | Obligatoria | Módulo de sanitización separado, con límite de longitud y detección de patrones de anulación |
| LLM02 — Sensitive Information Disclosure | Obligatoria | Credenciales solo por variable de entorno; el registro guarda metadatos, nunca contenido |
| LLM10 — Unbounded Consumption | Obligatoria | `slowapi` por API key + techo de `max_tokens` |
| **LLM07 — System Prompt Leakage** | **Elegida** | Canario en el system prompt + filtro de salida antes de responder |

**Por qué LLM07 como cuarta:** su verificación es binaria, no heurística. Se planta una
cadena única (`CANARIO-7F3A-NO-REVELAR`) en el system prompt; si aparece en una respuesta,
hubo fuga, sin ambigüedad. Eso la vuelve la mitigación más limpia de demostrar en el video,
que es donde se juegan 15 puntos. La alternativa considerada, LLM05 (Improper Output
Handling), exigiría que el gateway ejecutara algo generado por el modelo, lo que amplía el
alcance sin mejorar la demostración.

### 2. El límite de consumo es por API key

Cada aplicación cliente recibe su propia clave y su propio cupo. La prueba A4.2 lo
demuestra lanzando dos claves **desde la misma máquina**: si el límite estuviera por IP,
la segunda clave quedaría bloqueada sin haber consumido nada.

## Consecuencias

- El gateway necesita autenticar a sus clientes, no solo reenviar al proveedor. Es trabajo
  extra respecto a un límite por IP, pero es lo que corresponde a un gateway real.
- El canario obliga a que el system prompt sea fijo y controlado por el gateway: el cliente
  no puede enviar el suyo. Es una restricción deseable en una puerta única.
- Quedan fuera LLM03, LLM04, LLM05, LLM06, LLM08 y LLM09. El motivo de cada exclusión está
  documentado en `docs/owasp-mapping.md`, porque la rúbrica valora que el mapeo sea
  específico y razonado, no una lista copiada.
