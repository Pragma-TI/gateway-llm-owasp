# Backlog — Gateway LLM con Seguridad OWASP

Ordenado según el plan de 5 fases del documento del proyecto. Cada ítem se cierra cuando
**todos** sus criterios se cumplen y queda registrado en [bitacora.md](bitacora.md).

Estados: `PENDIENTE` · `EN CURSO` · `HECHO`

---

## PBI-01 — Fase 1: diseñar los ataques antes del código
**Estado:** HECHO · 3 de octubre

- [x] Elegidas las 4 categorías: LLM01, LLM02, LLM10 (obligatorias) + LLM07 (elegida).
- [x] `docs/casos-de-prueba.md` con el comportamiento esperado con y sin mitigación.
- [x] Pruebas ejecutables en `pruebas/`, parametrizadas por `MODO`.
- [x] Entorno Python del proyecto instalado.

---

## PBI-02 — Fase 2: gateway sin mitigaciones (línea base)
**Estado:** PENDIENTE

Punto de entrada único hacia Ollama, **sin ninguna protección**. Sirve para demostrar que
los ataques funcionan.

Criterios de aceptación:
- [ ] `POST /v1/chat` recibe un mensaje y devuelve la respuesta del modelo.
- [ ] `GET /health` reporta estado del gateway y del proveedor.
- [ ] System prompt del asistente del condominio, con el canario incrustado.
- [ ] Autenticación por `X-API-Key` (necesaria para el límite por clave del PBI-05).
- [ ] `MODO=baseline pytest` ejecutado: los 4 ataques funcionan y queda la evidencia.
- [ ] **Validación crítica:** al menos uno de los 3 ataques de LLM07 extrae el canario.
      Si ninguno lo logra, hay que diseñar ataques más fuertes antes de seguir.

---

## PBI-03 — Fase 3a: LLM01, sanitización de entrada
**Estado:** PENDIENTE

Criterios de aceptación:
- [ ] Módulo `sanitizacion.py` **separado y testeable de forma aislada**.
- [ ] Límite de longitud aplicado antes de construir el prompt.
- [ ] Separación explícita entre instrucciones del sistema y datos del usuario.
- [ ] `MODO=mitigado pytest pruebas/test_llm01_inyeccion.py` en verde.
- [ ] Documentado qué payloads **siguen pasando** pese a la mitigación.

---

## PBI-04 — Fase 3b: LLM02, credenciales y datos sensibles
**Estado:** PENDIENTE

Criterios de aceptación:
- [ ] Toda credencial se lee por variable de entorno; ninguna en el código.
- [ ] `.env` fuera del control de versiones.
- [ ] Nada con forma de credencial en el historial de git.
- [ ] `MODO=mitigado pytest pruebas/test_llm02_secretos.py` en verde.

---

## PBI-05 — Fase 3c: LLM10, límite de consumo
**Estado:** PENDIENTE

Criterios de aceptación:
- [ ] `slowapi` limitando **por API key, no por IP**.
- [ ] Techo de `max_tokens` aplicado y reportado en la respuesta.
- [ ] Al superar el límite responde 429 **sin llamar al proveedor**.
- [ ] La prueba de aislamiento entre claves (A4.2) en verde.

---

## PBI-06 — Fase 3d: LLM07, fuga del system prompt
**Estado:** PENDIENTE

Criterios de aceptación:
- [ ] Filtro de salida que detecta el canario antes de responder al cliente.
- [ ] La violación queda registrada (sin incluir el texto filtrado).
- [ ] `MODO=mitigado pytest pruebas/test_llm07_fuga_system_prompt.py` en verde.

---

## PBI-07 — Fase 4: registro seguro y degradación controlada
**Estado:** PENDIENTE

Criterios de aceptación:
- [ ] Log en JSON con `timestamp`, `endpoint`, `resultado` y `latencia_ms`.
- [ ] **Nunca** registra el prompt del usuario ni credenciales.
- [ ] Si Ollama falla, el cliente recibe un mensaje claro, nunca una traza interna.
- [ ] Métrica agregada tipo *Guardrail Violation Rate*: violaciones sobre total.

---

## PBI-08 — Fase 5: mapeo OWASP y entrega
**Estado:** PENDIENTE

Criterios de aceptación:
- [ ] `docs/owasp-mapping.md` completo, con pasos de reproducción verificados por un tercero.
- [ ] Los pares de evidencia `baseline_*` y `mitigado_*` presentes en `docs/evidencia/`.
- [ ] Guion del video con las 4 preguntas obligatorias y sus tiempos.
- [ ] Video grabado, de 30 minutos o menos, mostrando al menos un ataque burlando la
      protección y luego bloqueado por ella.

---

## Fuera del alcance, con motivo

| Categoría | Por qué no |
|---|---|
| LLM03 Supply Chain | Se mitiga fijando versiones, pero no se demuestra en vivo |
| LLM04 Data Poisoning | No se entrena ni ajusta ningún modelo |
| LLM05 Improper Output Handling | Exigiría que el gateway ejecutara salida del modelo; amplía el alcance sin mejorar la demostración |
| LLM06 Excessive Agency | El gateway no invoca herramientas |
| LLM08 Vector/Embeddings | No hay RAG |
| LLM09 Misinformation | Depende del modelo y del caso de uso, no del gateway |
