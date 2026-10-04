# Chuleta — frases cortas para decir mientras grabas

Para tener al lado del teclado. Cada bloque son dos o tres frases, no un discurso.

---

## Al empezar

> Esto es la puerta de entrada entre las aplicaciones de una administradora de edificios y
> un asistente de inteligencia artificial. Antes, cada aplicación llamaba al modelo por su
> cuenta. Ahora todas pasan por aquí, y aquí es donde controlo lo que pasa.

---

## PREGUNTA 1 · Las categorías

> Cubrí cuatro riesgos del estándar OWASP. Los elegí siguiendo el recorrido de una
> consulta: lo que entra, con qué credencial se identifica, cuánto consume y lo que sale.
>
> Las tres primeras las pedía el enunciado. La cuarta, la fuga del prompt de sistema, la
> elegí yo porque se comprueba sin discusión: puse una clave secreta dentro de las
> instrucciones del asistente. Si aparece en una respuesta, hubo fuga. Si no aparece, no
> la hubo.

**Si preguntan por las que faltan:**

> Las demás no dependen de este componente. Unas exigen controlar el entrenamiento del
> modelo, otras un buscador de documentos, otras que el gateway ejecute herramientas. Aquí
> no hay nada de eso.

---

## PREGUNTA 2 · Durante la demostración

### Al arrancar sin protección

> Voy a apagar todas las protecciones. Fíjense en la advertencia que suelta al arrancar.

### Después del ataque de inyección

> Ahí está. El asistente confirma que está en modo mantenimiento y dice que puede acceder a
> información de los propietarios. Nadie tocó el modelo: bastó con escribirle que las
> restricciones estaban desactivadas.

### Después del robo de instrucciones

> Y aquí entrega su configuración completa, con la clave secreta incluida. Esa clave solo
> existe dentro del asistente, así que no hay duda de que se filtró.

### Al ver las 14 consultas aceptadas

> Catorce seguidas, todas atendidas. Una aplicación con un error podría repetir esto mil
> veces y nadie se enteraría hasta que llegue la factura.

### Al mostrar el registro con el DNI

> El registro guardó la consulta entera, con el DNI y el teléfono. El propio sistema de
> auditoría se convirtió en la fuga.

### Al encender las protecciones

> Mismo código, misma consulta, cambio una sola variable al arrancar.

### Al repetir el ataque de inyección

> Es exactamente el mismo texto, carácter por carácter. Ahora lo rechaza y ni siquiera
> llega al modelo. No gastamos un token en procesarlo.

### Al ver el límite de consultas

> La número once ya se rechaza. Y esto es lo importante: con esa aplicación bloqueada, uso
> otra credencial desde esta misma máquina y responde con normalidad. Si hubiera limitado
> por dirección de red, habría castigado a una aplicación que no consumió nada.

### Al mostrar la consulta legítima

> Esta consulta normal funciona igual antes y después. El filtro no bloquea todo: bloquea
> los intentos de manipulación.

### Al mostrar el techo de tokens

> Pedí cien mil y aplicó quinientos doce. Y lo avisa en la respuesta, no lo hace en
> silencio.

---

## PREGUNTA 3 · Qué no registro

> Decidí no guardar ni la consulta ni la respuesta. Son el dato más útil para depurar y el
> más peligroso de almacenar: las preguntas de un propietario traen su DNI, su
> departamento y su deuda.
>
> Guardarlas significa crear una segunda copia de datos personales en un archivo de texto,
> fuera de la base de datos y de sus controles. Registro que pasó algo, no qué decía.

**Y el remate, mostrando las métricas:**

> La objeción típica es que sin el contenido no se puede auditar. Aquí está la respuesta:
> cuántas consultas hubo, cuántas se bloquearon y qué porcentaje representan. Todo sin
> haber guardado una sola pregunta.

---

## PREGUNTA 4 · La quinta mitigación

> Añadiría el manejo seguro de la salida, y por una razón práctica: el gateway ya tiene el
> punto exacto donde hacerlo, que es el filtro de respuesta que construí para la fuga.
>
> El riesgo concreto es este: hoy devuelvo el texto del modelo tal cual. Si la aplicación
> que lo recibe lo muestra en una web sin más, un modelo manipulado podría colar código
> que se ejecute en el navegador del propietario. El gateway es el último sitio donde eso
> se puede parar.

---

## Al cerrar · Los límites

> Antes de terminar, tres cosas que no funcionan del todo.
>
> La detección de ataques es una lista de patrones, no algo inteligente. Lo comprobé: el
> mismo ataque escrito en inglés pasa sin problema.
>
> También produce falsos positivos. Si un propietario escribe que el ascensor está en modo
> mantenimiento, lo bloqueo sin que haya hecho nada malo.
>
> Y de los cinco ataques que diseñé, algunos los rechaza el propio modelo y no mi código.
> Lo reporto así, porque no es mérito del gateway.

---

## Frase final

> Lo importante no es que los controles existan, sino que puedo demostrar que funcionan.
> El mismo ataque, apagado y encendido, con el resultado opuesto.
