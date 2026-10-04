# Mapeo OWASP Top 10 for LLM Applications (2025)

Documento central del entregable específico (25 puntos de la rúbrica).

**Regla de este documento:** una mitigación solo se marca como implementada cuando existe
evidencia reproducible de que funciona **y** de cómo se comportaba el sistema sin ella.

---

## Mitigaciones incluidas en el alcance

### LLM01 — Prompt Injection
| | |
|---|---|
| Riesgo concreto | Un usuario incrusta instrucciones en el texto para que el modelo ignore las reglas del sistema |
| Mitigación | Pendiente de implementar (PBI-04) |
| Cómo reproducir la evidencia | Pendiente |
| Línea base (sin mitigación) | Pendiente |
| Límites conocidos | La sanitización **reduce** el riesgo, no lo elimina. Documentar qué intentos siguen pasando |

### LLM02 — Sensitive Information Disclosure
| | |
|---|---|
| Riesgo concreto | Credenciales en el código o datos sensibles en los registros |
| Mitigación | Pendiente de implementar (PBI-02) |
| Cómo reproducir la evidencia | Pendiente |
| Línea base (sin mitigación) | Pendiente |
| Límites conocidos | Pendiente |

### LLM10 — Unbounded Consumption
| | |
|---|---|
| Riesgo concreto | Un cliente mal configurado o malicioso dispara el costo o satura el servicio |
| Mitigación | Pendiente de implementar (PBI-03) |
| Cómo reproducir la evidencia | Pendiente |
| Línea base (sin mitigación) | Pendiente |
| Límites conocidos | Pendiente |

---

## Categorías evaluadas y excluidas

| Código | Nombre | Por qué queda fuera |
|---|---|---|
| LLM03 | Supply Chain | Se mitiga parcialmente fijando versiones de dependencias; no se demuestra en vivo |
| LLM04 | Data and Model Poisoning | No se entrena ni ajusta ningún modelo en este alcance |
| LLM05 | Improper Output Handling | Candidato a incluir si sobra tiempo: validar la salida antes de devolverla |
| LLM06 | Excessive Agency | El gateway no ejecuta herramientas ni acciones |
| LLM07 | System Prompt Leakage | Candidato a incluir: probar si el prompt del sistema puede extraerse |
| LLM08 | Vector and Embedding Weaknesses | No hay RAG en este alcance |
| LLM09 | Misinformation | Fuera del alcance de un gateway: depende del modelo y del caso de uso |

---

## Referencia

OWASP Top 10 for Large Language Model Applications, edición 2025.
