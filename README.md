# Gateway LLM con Seguridad de Nivel Producción

Proyecto Final · Opción 04 — Curso Fundamentos de Arquitectura LLM (BSG Institute)

Puerta única de entrada entre las aplicaciones de una organización y el proveedor de
modelos de lenguaje, con cuatro mitigaciones del **OWASP Top 10 for LLM Applications
(2025)** aplicadas desde el diseño y **demostrables en vivo**, cada una con su línea base
sin protección como punto de comparación.

Caso de uso: asistente virtual de un edificio residencial (reglamento, cuotas e
incidencias), con datos ficticios.

## Estado

| | |
|---|---|
| Inicio | 24 de septiembre de 2026 |
| Entrega | ~6 de octubre de 2026 |
| Estado | Implementación completa y verificada · pendiente grabar el video |
| Pruebas | 32 con protección, 14 en línea base |

## Las cuatro categorías

| Categoría | Mitigación | Módulo |
|---|---|---|
| LLM01 Prompt Injection | Sanitización de entrada con 7 patrones y límite de longitud | `src/sanitizacion.py` |
| LLM02 Sensitive Information Disclosure | Credenciales por entorno; el log guarda metadatos, no contenido | `src/config.py`, `src/registro.py` |
| LLM07 System Prompt Leakage *(elegida)* | Canario en el system prompt + filtro de salida | `src/filtro_salida.py` |
| LLM10 Unbounded Consumption | `slowapi` **por API key** + techo de `max_tokens` | `src/main.py` |

## Resultados medidos

| Caso | Sin protección | Con protección |
|---|---|---|
| 5 ataques de inyección | HTTP 200; dos fueron obedecidos | HTTP 400 los cinco |
| Extracción del system prompt | El canario llegó al usuario | Bloqueado en entrada y en salida |
| 30 peticiones seguidas | 30 aceptadas | 10 aceptadas, 20 con HTTP 429 |
| Dos claves, misma IP | — | Una bloqueada, la otra sigue atendida |
| `max_tokens: 100000` | Reenviado tal cual | Recortado a 512 |
| Log de auditoría | DNI, teléfono y prompt en texto plano | Solo metadatos |
| Proveedor caído | HTTP 500 con la excepción interna | HTTP 503 con mensaje claro |

## Instalación

```bash
python -m venv venv
venv\Scripts\activate          # Windows · source venv/bin/activate en Linux
pip install -r requirements.txt
```

Requiere [Ollama](https://ollama.com) corriendo con el modelo `llama3.2:3b`:

```bash
ollama pull llama3.2:3b
```

## Ejecución

```bash
# Modo protegido (predeterminado)
uvicorn main:app --app-dir src --port 8010

# Línea base, sin ninguna protección (solo para la demostración)
GATEWAY_MODO=baseline uvicorn main:app --app-dir src --port 8010
```

| Endpoint | Para qué |
|---|---|
| `POST /v1/chat` | Punto de entrada único. Requiere cabecera `X-API-Key` |
| `GET /health` | Estado del gateway, del proveedor y de cada mitigación |
| `GET /metricas` | *Guardrail Violation Rate*: violaciones sobre total de peticiones |

## Reproducir la evidencia

```bash
MODO=baseline pytest -v      # contra el gateway en modo baseline
MODO=mitigado pytest -v      # contra el gateway protegido
```

Cada corrida escribe en `docs/evidencia/<modo>_<caso>.json`. El par de archivos
`baseline_*` / `mitigado_*` del mismo caso es la evidencia del antes y después.

Las pruebas del módulo de sanitización y las de degradación **no necesitan el gateway
levantado**:

```bash
pytest pruebas/test_sanitizacion_unitaria.py pruebas/test_degradacion.py -v
```

## Documentación

| Documento | Contenido |
|---|---|
| [docs/owasp-mapping.md](docs/owasp-mapping.md) | **Documento central**: cada categoría, su mitigación y cómo reproducir la evidencia |
| [docs/casos-de-prueba.md](docs/casos-de-prueba.md) | Diseño de los ataques, escritos antes que las defensas |
| [docs/guion-video.md](docs/guion-video.md) | Guion del video con tiempos |
| [docs/bitacora.md](docs/bitacora.md) | Registro fechado, incluidos los errores y lo que quedó sin probar |
| [docs/architecture/](docs/architecture/) | Decisiones de arquitectura (ADR) |
| [docs/evidencia/](docs/evidencia/) | Salidas de las pruebas |

## Límites declarados

- La detección de inyección es **una lista de patrones, no un clasificador**: un ataque
  redactado de otra forma puede pasar. Por eso el filtro de salida actúa como segunda capa.
- En la línea base, **2 de los 5 ataques fueron rechazados por el propio modelo**, no por
  el gateway. Se reportan como tales.
- Las mediciones de latencia corresponden a Ollama local en un equipo concreto y no
  representan a un proveedor en la nube.

## Entregables del curso

- [x] Repositorio con el gateway funcional
- [x] Documento de mapeo OWASP con instrucciones de reproducción
- [x] Casos de prueba de cada mitigación, con la línea base
- [ ] Video explicativo (máx. 30 minutos) — guion listo en `docs/guion-video.md`
