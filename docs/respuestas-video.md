# Las cuatro respuestas del video

Las preguntas obligatorias del enunciado, con la respuesta preparada y los datos reales
medidos en este proyecto. Reformula con tus palabras; los números no.

---

# PREGUNTA 1 · ¿Qué categorías eligieron y por qué son las más relevantes para un gateway?

## La respuesta corta

Cubrí cuatro. Tres las fija el enunciado —LLM01 inyección de prompts, LLM02 exposición de
información sensible y LLM10 consumo sin límite— y la cuarta la elegí yo: **LLM07, fuga
del prompt de sistema**.

## El argumento que las une

Un gateway es una puerta, y lo que importa en una puerta es **lo que cruza por ella**. Las
cuatro categorías que elegí son exactamente los cuatro momentos de una petición:

| Momento | Riesgo | Categoría |
|---|---|---|
| Lo que **entra** | Texto que intenta manipular al modelo | **LLM01** |
| Con qué **se identifica** y qué queda guardado | Credenciales y datos personales | **LLM02** |
| **Cuánto** se consume | Gasto y saturación sin control | **LLM10** |
| Lo que **sale** | El modelo revela su configuración | **LLM07** |

No es una lista escogida por conveniencia: es el recorrido completo de una consulta a
través del componente.

## Por qué LLM07 y no otra

Elegí LLM07 por una razón práctica: **su verificación es binaria**. Puse una cadena única
dentro de las instrucciones del asistente, el canario. Si esa cadena aparece en una
respuesta, hubo fuga; si no aparece, no la hubo. Sin interpretación, sin heurística.

Consideré **LLM05, manejo inadecuado de la salida**, y la descarté porque exigiría que el
gateway ejecutara lo que el modelo genera. Eso amplía el alcance del componente sin
mejorar la demostración.

## Por qué las demás quedan fuera

No por falta de tiempo, sino porque **no son responsabilidad de este componente**:

- **LLM04, envenenamiento de datos**: exige control del entrenamiento del modelo.
- **LLM08, debilidades de embeddings**: exige un sistema de búsqueda de documentos, y aquí no hay.
- **LLM06, agencia excesiva**: exige que el gateway invoque herramientas, y este solo reenvía.
- **LLM03, cadena de suministro**: la mitigo fijando versiones en `requirements.txt`, pero no puedo demostrarla en vivo.

📺 **Qué mostrar:** `GET /health` con las cinco protecciones en `true`, y `docs/owasp-mapping.md`.

---

# PREGUNTA 2 · El ataque sin protección y el mismo caso con protección

> Esta es la pregunta que vale los puntos. La respuesta es la demostración en vivo, no un
> discurso. Sigue los pasos de `docs/pasos-practica.md`.

## Resumen de lo medido

| Mitigación | Sin protección | Con protección |
|---|---|---|
| **LLM01** · inyección | HTTP 200 · el asistente confirma estar "en modo mantenimiento" y dice poder acceder a información de propietarios | **HTTP 400** · rechazado antes de llegar al modelo |
| **LLM02** · registro | El log guarda el DNI, el teléfono y la consulta completa en texto plano | **`"contenido_omitido": true`** · cero coincidencias del DNI |
| **LLM07** · fuga | El asistente entrega sus instrucciones con el canario incluido | **HTTP 400** en la entrada, y el filtro de salida como segunda capa |
| **LLM10** · consumo | 14 de 14 consultas aceptadas · `max_tokens` 100000 reenviado tal cual | **10 aceptadas y 4 con HTTP 429** · techo aplicado de **512** |

## Lo que debes decir mientras lo muestras

**En el ataque de inyección, sin protección:**
> Miren la respuesta: el asistente confirma que está en modo mantenimiento y enumera cosas
> que no debería poder hacer. Nadie tocó el modelo. Bastó con escribirle que las
> restricciones estaban desactivadas.

**Con protección, con el mismo texto:**
> Es exactamente la misma consulta, carácter por carácter. Ahora devuelve 400 y ni siquiera
> llega al modelo: no gastamos un token en procesarla.

**En el límite de consumo:**
> La consulta número once se rechaza. Y aquí está el detalle que importa: con esa
> aplicación bloqueada, lanzo una consulta con otra credencial **desde la misma máquina** y
> se atiende con normalidad. Si hubiera limitado por dirección de red, habría castigado a
> una aplicación que no consumió nada.

**Y la consulta legítima, en los dos escenarios:**
> Esta consulta normal funciona igual antes y después. El filtro no bloquea todo: bloquea
> los intentos de manipulación.

## La segunda capa de LLM07

> Tengo que ser honesto con algo: los ataques de fuga se detienen en la entrada, así que el
> filtro de salida nunca llegaba a actuar. Eso significa que no estaba demostrado. Lo probé
> apagando solo la primera capa: el modelo sí reveló el canario, y el filtro lo interceptó
> antes de entregárselo al usuario. El registro lo anotó como "bloqueado por fuga".

---

# PREGUNTA 3 · ¿Qué decidieron NO registrar y por qué?

## La respuesta corta

Decidí **no registrar el contenido de la consulta ni la respuesta del modelo**. En el
código son dos campos concretos, `prompt_usuario` y `respuesta_modelo`, que se eliminan
antes de escribir cada línea.

## Por qué es la decisión correcta

**Primero, por lo que contienen.** Las consultas de un propietario traen su DNI, su número
de departamento y su situación de deuda. Guardarlas significa crear **una segunda copia de
datos personales**, en un archivo de texto plano, fuera de la base de datos y de sus
controles de acceso.

**Segundo, porque es exactamente lo que advierte LLM02.** El error común que describe el
estándar es guardar el prompt completo "por si sirve para depurar". El sistema de auditoría
se convierte así en la fuga que debía ayudar a detectar.

**Tercero, porque no hace falta.** Esta es la parte que convence: sigo pudiendo auditar.

## Lo que sí registro

```json
{"timestamp": "...", "endpoint": "/v1/chat", "cliente": "App Portal Propietarios",
 "resultado": "ok", "latencia_ms": 5485, "tokens_entrada": 238, "tokens_salida": 45,
 "violacion": false, "contenido_omitido": true}
```

Con eso puedo responder: cuántas consultas hubo, qué aplicación las hizo, cuánto tardaron,
cuántos tokens costaron y cuántas se bloquearon por seguridad. **Todo sin guardar una sola
pregunta.**

El endpoint `/metricas` lo resume en el indicador *Guardrail Violation Rate*, tomado de la
guía de observabilidad de agentes: violaciones sobre total de peticiones.

## Si te objetan "sin el contenido no puedes depurar"

> Es cierto que se pierde capacidad de depuración, y es un intercambio consciente. Si en
> producción hiciera falta, la salida sería guardar el contenido cifrado, con acceso
> restringido y borrado automático a los pocos días. Lo que no es defendible es dejarlo en
> texto plano en un archivo junto a la aplicación.

📺 **Qué mostrar:** `src/registro.py` con la línea `CAMPOS_SENSIBLES`, las dos líneas de log
lado a lado, la búsqueda del DNI que no encuentra nada, y `/metricas`.

---

# PREGUNTA 4 · La quinta mitigación, con más tiempo

## La respuesta corta

**LLM05, manejo inadecuado de la salida.**

## Por qué esa

**Porque el gateway ya tiene el punto exacto donde aplicarla.** El filtro de salida que
construí para LLM07 ya intercepta cada respuesta antes de entregarla. Añadir LLM05 sería
extender ese mismo punto: validar que la respuesta no contenga comandos, SQL ni HTML
ejecutable antes de pasársela a la aplicación cliente.

**Y porque es la única del resto del listado que corresponde a una puerta de entrada.** Las
demás exigen controlar partes del sistema que un gateway no toca: el entrenamiento del
modelo, el buscador de documentos o las herramientas que el modelo invoca.

## El riesgo concreto que cubriría

Hoy mi gateway devuelve el texto del modelo tal cual a la aplicación cliente. Si esa
aplicación lo pinta en una página web sin escapar el contenido, un modelo manipulado podría
devolver código que se ejecute en el navegador del propietario. **El gateway es el último
punto donde eso se puede parar antes de salir.**

## Si te preguntan por qué no la hiciste ahora

> Porque el enunciado pedía cuatro categorías demostrables, y preferí demostrar bien cuatro
> que mencionar cinco. LLM05 habría exigido construir también una aplicación cliente que
> renderizara la salida, para poder mostrar el ataque de verdad. Sin esa parte, la
> mitigación habría quedado "de papel", que es justamente el error que el enunciado
> advierte.

---

# CIERRE · Los límites que debes decir en voz alta

No los escondas: suman credibilidad.

1. **La detección de inyección es una lista de patrones, no un clasificador.** Lo comprobé:
   el mismo ataque escrito en inglés atraviesa el filtro, porque los patrones están en
   español.
2. **Produce falsos positivos.** Un propietario que escriba "el ascensor está en modo
   mantenimiento" queda bloqueado sin haber hecho nada malo.
3. **De los cinco ataques de inyección, algunos los rechaza el propio modelo**, no mi
   código. Lo reporto así: no es mérito del gateway.
4. **Las métricas viven en memoria** y se reinician con el servicio. En producción irían a
   una base de datos.
5. **Todo se midió contra un modelo local concreto.** Con otro modelo, los resultados de
   los ataques podrían variar; lo que no cambia es el comportamiento del gateway.
