# ADR-001 — Alcance del gateway y proveedor de inferencia

- **Fecha:** 24 de septiembre de 2026
- **Estado:** Propuesta (pendiente de confirmación)

## Contexto

El proyecto exige construir un gateway LLM con mitigaciones OWASP demostrables. Hay que
decidir contra qué proveedor de inferencia se demuestra, sabiendo que:

- No se cuenta con cuenta de Google Cloud ni con API keys de pago para el curso.
- Existe una instalación local de Ollama con los modelos `llama3.2:3b`, `mistral`,
  `phi3:mini` y `nomic-embed-text`.
- La rúbrica premia la evidencia reproducible, no la cantidad de proveedores soportados.

## Decisión

Usar **Ollama local como proveedor de demostración**, con la capa de proveedor aislada
detrás de una interfaz para poder agregar un proveedor de nube sin reescribir el gateway.

## Consecuencias

**A favor:**
- Costo cero y sin límites de cuota, lo que permite repetir las pruebas de consumo (LLM10)
  tantas veces como haga falta.
- Las demostraciones funcionan sin conexión, útil para grabar el video.
- Ningún dato de prueba sale del equipo.

**En contra:**
- No se ejercita el manejo real de una API key de terceros. Se compensa implementando
  igualmente la gestión de secretos (PBI-02), con una credencial de proveedor de nube
  configurable aunque no se use en la demostración.
- La latencia local no representa la de un proveedor de nube; los números de rendimiento
  deben presentarse como propios del entorno local, sin extrapolar.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Solo proveedor de nube | Requiere pagar; el límite de cuota del proveedor interfiere con la prueba de consumo |
| Varios proveedores reales | Alarga el alcance sin sumar puntos: la rúbrica evalúa mitigaciones, no cobertura de proveedores |
