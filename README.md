# Gateway LLM con Seguridad de Nivel Producción

Proyecto Final · Opción 04 — Curso Fundamentos de Arquitectura LLM (BSG Institute)

Puerta única de entrada entre las aplicaciones de una organización y los proveedores de
modelos de lenguaje, con mitigaciones del **OWASP Top 10 for LLM Applications (2025)**
aplicadas desde el diseño y **demostrables en vivo**.

## Estado del proyecto

| | |
|---|---|
| Fecha de inicio | 24 de septiembre de 2026 |
| Entrega estimada | ~6 de octubre de 2026 |
| Estado actual | Diseño — sin código todavía |

## Qué hace (alcance previsto)

1. Recibe peticiones de aplicaciones clientes en un único endpoint.
2. Aplica controles de seguridad **antes** de llamar al modelo.
3. Enruta la petición al proveedor de inferencia configurado.
4. Registra cada llamada para auditoría y control de consumo.
5. Devuelve la respuesta, o el error del control que la bloqueó.

## Proveedor de inferencia

Ollama local (`llama3.2:3b`). Ver [ADR-001](docs/architecture/ADR-001-alcance-y-proveedor.md).

## Documentación

| Documento | Contenido |
|---|---|
| [docs/backlog.md](docs/backlog.md) | Ítems de trabajo (PBI) con criterios de aceptación |
| [docs/owasp-mapping.md](docs/owasp-mapping.md) | Cada categoría OWASP → mitigación → cómo reproducir la evidencia |
| [docs/architecture/](docs/architecture/) | Decisiones de arquitectura (ADR) |
| [docs/bitacora.md](docs/bitacora.md) | Registro fechado de lo hecho, verificado y pendiente |
| [docs/evidencia/](docs/evidencia/) | Salidas de las pruebas: línea base vs. con mitigación |

## Cómo ejecutar

Pendiente: se documenta cuando exista el primer endpoint.

## Entregables del curso

- [ ] Repositorio con el gateway funcional
- [ ] Documento de mapeo OWASP con instrucciones de reproducción
- [ ] Casos de prueba que demuestren cada mitigación, **incluida la línea base sin ella**
- [ ] Video explicativo (máx. 30 minutos)
