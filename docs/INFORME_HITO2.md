# Hito 2 · Zancada conectado a Gemini

Sistemas Inteligentes Aplicados · ITU UNCuyo · 2026

**Integrante:** Zoe Garcia Badiola
**Equipo:** Zoe Garcia Badiola, Ignacio Morichetti, Matias Lopez, Gonzalo Laspada, Luciano Malanca 
**Bot de prueba:** [@Zancada_ZoeGBR_bot](https://t.me/Zancada_ZoeGBR_bot)
**Repositorio:** https://github.com/ZogeGBR/ZANCADA

## 1. Qué se entrega

Zancada, el coach de running del equipo, en el nivel de la v3:

- **Gemini con la Interactions API sin estado** (`store=False`, `client.aio.interactions.create`). La clave y el modelo (`gemini-3.5-flash-lite`) se leen del `.env`.
- **Historial en SQLite** con `aiosqlite` (`db.py`): en cada consulta se envían a Gemini los últimos 20 mensajes del usuario más el mensaje nuevo, y solo se guarda el intercambio si la consulta salió bien.
- **Comando `/olvidar`** para borrar la conversación del usuario.
- **Prompt de sistema** en `prompts.py`.
- Se mantienen `/start`, `/help` y `/ritmo` de la v1, y se agregan el manejo de errores por código (429, 401/403 y otros), el aviso para mensajes que no son texto y el ignorado de mensajes editados.

El repositorio incluye `.env.example` y `.gitignore`, y **no** contiene el `.env` ni archivos `.db`.

## 2. Prompt de sistema

Está en [`prompts.py`](../prompts.py) y cubre los cinco aspectos de la lectura de la Clase 2:

| Aspecto | Cómo lo cubre Zancada |
|---|---|
| Identidad | Coach de running que conversa con corredores amateurs; cercano y motivador, en español rioplatense con voseo. |
| Tarea y alcance | Ritmos, planificación de la salida, entrenamiento y hábitos de corredor. Usa lo que el usuario contó antes. Redirige con amabilidad lo que no es running. Ante dolor o lesión no diagnostica y recomienda consultar a un profesional. No pide datos personales ni sensibles. |
| Estilo | Muy cálida y cercana, frases cortas, tono técnico solo cuando hace falta, cierra con una pregunta o propuesta. |
| Formato | De 2 a 4 emojis por mensaje, relacionados con lo que dice. |
| Honestidad | No inventa precios, fechas, horarios, clima ni estadísticas; avisa cuando no lo sabe y sugiere dónde verificarlo. |

Texto completo (versión final, después del ajuste de la sección 4):

```text
# IDENTIDAD
Sos Zancada, un coach de running que conversa por Telegram con corredores
amateurs, desde quienes recién empiezan hasta quienes preparan 10K o 21K.
Sos cercano y motivador, como el entrenador de un grupo de running.
Hablás en español rioplatense, con voseo ("salí", "probá", "contame").

# TAREA Y ALCANCE
Ayudás con: ritmos y tiempos estimados, planificación de la salida del día,
ideas de entrenamiento para 5K, 10K, 21K y 42K, hábitos de corredor
(hidratación, ropa, descanso, constancia) y motivación.
Todavía NO podés consultar el clima real, ni guardar entrenamientos, ni
buscar nada en internet. Si te piden algo de eso, decilo con naturalidad y
ofrecé lo que sí podés hacer (por ejemplo, el comando /ritmo para calcular
ritmos).
Usá lo que el usuario te contó antes en la conversación (su nivel, su
objetivo, sus horarios, sus gustos) para que cada respuesta sea personal.
No le vuelvas a preguntar lo que ya te dijo.
Si te preguntan algo que no tiene que ver con correr o el entrenamiento
(política, tareas escolares, programación, recetas, etc.), no lo respondas:
decí con amabilidad que ahí no podés ayudar y redirigí la charla hacia el
running.
Ante dolor, lesión, mareos u otro síntoma, nunca diagnostiques ni receses
nada: recomendá consultar a un profesional de la salud.
No pidas datos personales ni sensibles (documento, dirección, teléfono,
historia clínica). Si el usuario los comparte, sugerile que no lo haga en este
chat.

# ESTILO
Sos muy cálida y cercana, como una amiga que corre con el grupo: celebrás los
avances del usuario, lo alentás con entusiasmo y le hablás con cariño.
Usá frases cortas y directas. Si hace falta, pasá a un tono técnico
(ritmo en min/km, esfuerzo percibido de 1 a 10), pero explicalo simple.
Cerrá con una pregunta o una propuesta breve para que la conversación siga.

# FORMATO
Usá emojis en casi todas las respuestas, de 2 a 4 por mensaje, relacionados
con lo que estás diciendo (🏃‍♀️ 💪 🍌 🌙 ⏱️ 😊), para que el chat se sienta
alegre y cercano.

# HONESTIDAD
No inventes datos que no podés saber con certeza: precios, fechas y
horarios de carreras, inscripciones, el clima de mañana, resultados o
marcas de otras personas, ni estadísticas. En esos casos decí claramente
que no lo sabés o que no tenés acceso a esa información, y sugerí dónde
verificarla (la página oficial de la carrera, un pronóstico del tiempo).
Las estimaciones de tiempos son aproximadas y hay que presentarlas como tales.
Si no estás seguro de algo, decilo.
```

## 3. Conversación de prueba

Conversación con el bot del equipo, en el orden pedido por la consigna.

| # | Qué se escribió | Qué demuestra | Captura |
|---|---|---|---|
| 1 | "Corro de noche después del trabajo y mi meta son los 10K en 55 minutos" | Entiende y responde en tono con su personalidad | [01](capturas/01_inicio_dato_y_conversacion.png) |
| 2 | "Corro 3 veces por semana, hace un mes que empecé" y "¿Qué conviene comer antes de salir?" | La conversación fluye | [01](capturas/01_inicio_dato_y_conversacion.png), [02](capturas/02_ajuste_antes_memoria_y_alcance.png) |
| 3 | "¿Qué ritmo tengo que llevar para cumplir mi meta?" | Memoria: responde con los 10K en 55 minutos (5:30 min/km) sin que se repita el dato | [02](capturas/02_ajuste_antes_memoria_y_alcance.png) |
| 4 | Se reinició el bot (Ctrl+C y `python bot.py`) y se preguntó "¿Te acordás cuál es mi meta?" | Persistencia: la meta de 10K en 55 minutos sigue recordada | [03](capturas/03_alcance_persistencia_y_honestidad.png), [04](capturas/04_ajuste_despues.png) |
| 5 | "¿Me ayudás con una ecuación de segundo grado?" | Alcance: dice con amabilidad que su especialidad es el running y propone armar un entrenamiento | [02](capturas/02_ajuste_antes_memoria_y_alcance.png), [03](capturas/03_alcance_persistencia_y_honestidad.png) |
| 6 | "¿Cuánto sale la próxima 10K de mi ciudad y a qué hora largan?" | Honestidad: aclara que no tiene acceso a fechas, precios ni horarios y manda a la página oficial de la carrera | [03](capturas/03_alcance_persistencia_y_honestidad.png), [04](capturas/04_ajuste_despues.png) |

### Capturas

**01 · Inicio, dato del usuario y conversación**

![Captura 01](capturas/01_inicio_dato_y_conversacion.png)

**02 · Respuesta antes del ajuste, memoria y alcance**

![Captura 02](capturas/02_ajuste_antes_memoria_y_alcance.png)

**03 · Alcance, persistencia y honestidad**

![Captura 03](capturas/03_alcance_persistencia_y_honestidad.png)

**04 · Respuesta después del ajuste del prompt**

![Captura 04](capturas/04_ajuste_despues.png)

## 4. Ajuste del prompt de sistema

Al probar el bot, la respuesta a "¿Qué conviene comer antes de salir?" fue correcta pero fría y sin un solo emoji: *"Para correr de noche, lo mejor es algo liviano y rápido de digerir una hora antes, tipo una tostada con mermelada, media banana o unas galletitas de agua. No te llenes mucho para no ir con fiaca. ¿Cómo te viene cayendo la comida a esa hora?"*. Lo atribuimos a que el prompt pedía "alentá sin exagerar" y usar emojis "de vez en cuando, sin abusar". Reescribimos el bloque de estilo para que Zancada sea muy cálida y cercana, como una amiga del grupo de running que celebra los avances del usuario, y pedimos en el bloque de formato de 2 a 4 emojis por mensaje relacionados con lo que dice. Con el cambio, la misma pregunta recibió una respuesta más afectuosa y con emojis (*"¡Te recontra entiendo, lo habíamos hablado recién! Como vas a salir de noche después de laburar, lo ideal es meter algo liviano y rápido de digerir una hora antes, como media banana, una tostada con mermelada o unas galletitas de agua 🍌🍞 […] ¿Ya tenés pensado qué vas a comer hoy antes de arrancar? 😊"*), manteniendo el mismo contenido.

## 5. Checklist del hito

- [x] El repositorio tiene `.env.example` y `.gitignore`, y no tiene ni `.env` ni archivos `.db`.
- [x] El bot usa la Interactions API sin estado, con el modelo leído del `.env`.
- [x] El prompt de sistema cubre los cinco aspectos.
- [ ] Las capturas muestran los seis pasos de la conversación de prueba, incluido el reinicio. *(confirmar que la captura del paso 4 es posterior al reinicio del bot y tildar)*
- [x] El párrafo describe un ajuste concreto del prompt y su efecto.

## 6. Cómo ejecutarlo

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
python -m pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
python bot.py
```

En el `.env`, reemplazar los valores de ejemplo por el token de BotFather, la clave de Google AI Studio y el modelo (`gemini-3.5-flash-lite`). Los comandos del bot están en [`comandos_botfather.txt`](../comandos_botfather.txt).

## 7. Conversación de prueba de Ignacio Morichetti

**Integrante:** Ignacio Morichetti
**Bot de prueba:** [@Zancada_MorichettiRamal_hito2bot](https://t.me/Zancada_MorichettiRamal_hito2bot)

> **Aclaración.** Estas capturas no se hicieron con el código de este repositorio, sino con la versión del Hito 2 que Ignacio armó por separado para compararla con esta: <https://github.com/IgnacioMorichetti/zancada>. Es el mismo bot (Zancada, coach de running) en el nivel de la v3, con Interactions API sin estado, historial en SQLite y `/olvidar`, pero con su propio `prompts.py`. Por eso algunos textos difieren de los de este repo (por ejemplo, la respuesta de `/olvidar` y el uso de emojis).

### Conversación de prueba

| # | Qué se escribió | Qué demuestra | Captura |
|---|---|---|---|
| 1 | "Hola! Ya soy un poco experimentado en correr, corro todas las semanas unos 30 km pero me estoy preparando para una maratón el 2 de mayo del 2027" | Entiende y responde en tono con su personalidad | [01](capturas/ignacio/01_dato_del_usuario_y_conversacion.png) |
| 2 | "Entreno 6 días a la semana, pero corro 3 de esos unicamente, en general corro uno de 5 o 7 km, otro de 10km y uno largo de 14 o 16 km. Armemos un plan ¿Cómo entro en calor antes del fondo largo? y ¿Qué me conviene comer antes de salir?" (enviado en un solo mensaje) | La conversación fluye: responde las dos preguntas y ofrece armar el plan | [01](capturas/ignacio/01_dato_del_usuario_y_conversacion.png), [02](capturas/ignacio/02_conversacion_y_pregunta_de_memoria.png) |
| 3 | "¿Me conviene correr una carrera de 21K el mes que viene como preparación?" | Memoria: la ubica como parte de la preparación para los 42K y tiene en cuenta el fondo largo de 16 km, sin que se repitan los datos | [02](capturas/ignacio/02_conversacion_y_pregunta_de_memoria.png), [03](capturas/ignacio/03_memoria.png) |
| 4 | Se reinició el bot (Ctrl+C a las 15:21:09 y `python bot.py` a las 15:21:14) y se preguntó "¿Te acordás para qué carrera me preparo y cuántos km corro por semana?" | Persistencia: recuerda la maratón del 2 de mayo de 2027 y los 30 km semanales en tres salidas | [04](capturas/ignacio/04_reinicio_del_bot_terminal.png), [05](capturas/ignacio/05_persistencia_y_alcance.png) |
| 5 | "¿Me pasás una receta para hacer pizza?" | Alcance: dice con buena onda que lo suyo es el running y propone volver al entrenamiento | [05](capturas/ignacio/05_persistencia_y_alcance.png), [06](capturas/ignacio/06_alcance_y_honestidad.png) |
| 6 | "¿Cuánto sale la inscripción a la Maratón Internacional de Mendoza y a qué hora larga?" | Honestidad: aclara que no tiene el dato confirmado y sugiere la página oficial de la carrera | [06](capturas/ignacio/06_alcance_y_honestidad.png) |

### Capturas

**01 · Dato del usuario y comienzo de la conversación** (después de `/olvidar`)

![Captura 01 de Ignacio](capturas/ignacio/01_dato_del_usuario_y_conversacion.png)

**02 · Conversación y pregunta de memoria**

![Captura 02 de Ignacio](capturas/ignacio/02_conversacion_y_pregunta_de_memoria.png)

**03 · Memoria**

![Captura 03 de Ignacio](capturas/ignacio/03_memoria.png)

**04 · Reinicio del bot en la terminal** (se tapó el id de usuario de Telegram)

![Captura 04 de Ignacio](capturas/ignacio/04_reinicio_del_bot_terminal.png)

**05 · Persistencia después del reinicio y alcance**

![Captura 05 de Ignacio](capturas/ignacio/05_persistencia_y_alcance.png)

**06 · Alcance y honestidad**

![Captura 06 de Ignacio](capturas/ignacio/06_alcance_y_honestidad.png)

### Ajuste del prompt de sistema

En la primera prueba, al contarle que corro 30 km por semana y que me preparo para una maratón, el bot cerró la respuesta con dos preguntas juntas: *"¿cuántos días por semana venís entrenando y cómo los distribuís?, ¿te gustaría que armemos un plan semanal para empezar a ordenar las próximas semanas?"* (captura 07). En un chat uno contesta una sola y la otra se pierde. El prompt ya pedía "una sola pregunta concreta", pero solo para el caso en que faltara un dato (captura 08, línea 33). En `prompts.py` se reemplazó esa regla por una más directa y con el motivo explicado: *"Hacé como máximo una pregunta por mensaje, y nunca dos seguidas: en un chat el corredor contesta una sola y la otra se pierde"*. Después del cambio, el mismo mensaje recibió una respuesta que cierra con un único pedido: *"contame qué días de la semana preferís entrenar y cuántas veces salís habitualmente"* (captura 01).

**07 · Respuesta antes del ajuste: dos preguntas juntas**

![Captura 07 de Ignacio](capturas/ignacio/07_ajuste_antes_dos_preguntas.png)

**08 · `prompts.py` antes del ajuste**

![Captura 08 de Ignacio](capturas/ignacio/08_ajuste_prompt_antes.png)

## 8. Conversación de prueba de Gonzalo Laspada

**Integrante:** Gonzalo Laspada
**Bot de prueba:** Zancada Gonzalo

Las capturas se hicieron con el código de este repositorio, corriendo el bot en la computadora de Gonzalo.

### Conversación de prueba

| # | Qué se escribió | Qué demuestra | Captura |
|---|---|---|---|
| 1 | "Corro de noche después del trabajo y mi meta son los 10K en 55 minutos" (después de `/olvidar`) | Entiende y responde en tono con su personalidad: calcula el ritmo de 5:30 min/km y pregunta cómo viene entrenando | [01](capturas/Gonzalo/01_dato_del_usuario_y_conversacion.png) |
| 2 | "Corro 3 veces por semana, hace un mes que empecé" y "¿Qué conviene comer antes de salir?" (enviado en un solo mensaje) | La conversación fluye: lo felicita por la constancia y le recomienda algo liviano antes de salir de noche | [02](capturas/Gonzalo/02_conversacion_y_pregunta_de_memoria.png) |
| 3 | "¿Qué ritmo tengo que llevar para cumplir mi meta?" | Memoria: responde con los 10K en 55 minutos (5:30 min/km) sin que se repita el dato | [03](capturas/Gonzalo/03_memoria.png) |
| 4 | Se reinició el bot (Ctrl+C a las 19:22:27 y `python bot.py` a las 19:22:33) y se preguntó "¿Te acordás cuál es mi meta?" | Persistencia: recuerda los 10K en 55 minutos y las tres salidas por semana desde hace un mes | [04](capturas/Gonzalo/04_reinicio_del_bot.png), [05](capturas/Gonzalo/05_persistencia_y_alcance.png) |
| 5 | "¿Me ayudás a resolver una ecuación de segundo grado?" | Alcance: dice con humor que eso no es lo suyo y vuelve a ofrecer ayuda con el running | [06](capturas/Gonzalo/06_alcance.png) |
| 6 | "¿Cuánto sale la próxima 10K de mi ciudad y a qué hora largan?" | Honestidad: aclara que no tiene acceso a internet ni sabe de qué ciudad es, y sugiere la página oficial o las redes de la organización | [07](capturas/Gonzalo/07_honestidad.png) |

### Capturas

**01 · Dato del usuario y comienzo de la conversación** (después de `/olvidar`)

![Captura 01 de Gonzalo](capturas/Gonzalo/01_dato_del_usuario_y_conversacion.png)

**02 · Conversación**

![Captura 02 de Gonzalo](capturas/Gonzalo/02_conversacion_y_pregunta_de_memoria.png)

**03 · Memoria**

![Captura 03 de Gonzalo](capturas/Gonzalo/03_memoria.png)

**04 · Reinicio del bot en la terminal**

![Captura 04 de Gonzalo](capturas/Gonzalo/04_reinicio_del_bot.png)

**05 · Persistencia después del reinicio**

![Captura 05 de Gonzalo](capturas/Gonzalo/05_persistencia_y_alcance.png)

**06 · Alcance**

![Captura 06 de Gonzalo](capturas/Gonzalo/06_alcance.png)

**07 · Honestidad**

![Captura 07 de Gonzalo](capturas/Gonzalo/07_honestidad.png)

### Ajuste del prompt de sistema

**08 · `prompts.py` con el bloque ESTILO antes del ajuste de la sección 4** (línea 37 resaltada: *"Sos cercano y directo, como un entrenador que conoce bien su oficio: alentás con medida, sin exagerar, y priorizás dar información útil."*)

![Captura 08 de Gonzalo](capturas/Gonzalo/cambio_prompt.py.png)

## 9. Conversación de prueba de Matías López

**Integrante:** Matías López
**Bot de prueba:** [@Zancada_Lopez_bot](http://t.me/Zancada_Lopez_bot)

> **Aclaración.** Las capturas se realizaron ejecutando el código de este repositorio de forma local en la computadora de Matías con su propio bot de prueba en Telegram (`@Zancada_Lopez_bot`). Para la sección de ajuste del prompt se probó una variante propia del bloque `# ESTILO` en `prompts.py` para evaluar el cambio de personalidad entre el tono de "amiga de grupo de running" y el de un "entrenador honesto, serio y motivacional".

### Conversación de prueba

| # | Qué se escribió | Qué demuestra | Captura |
|---|---|---|---|
| 1 | "Corro en la noche después del trabajo y mi meta son los 10k en 55 minutos" (después de `/start`) | Entiende y responde en tono con su personalidad: celebra la meta y consulta cómo viene entrenando | [01](capturas/Matías/01.jpeg) |
| 2 | "Corro 3 veces por semana, hace un mes que empecé" "¿Qué conviene comer antes de salir?" | La conversación fluye: felicita por la constancia de las tres salidas y recomienda opciones livianas e hidratación para la noche | [02](capturas/Matías/02.jpeg) |
| 3 | "¿Qué ritmo tengo que llevar para cumplir mi meta?" | Memoria: responde con los 10K en 55 minutos (5:30 min/km) y las tres salidas semanales sin que se repita el dato | [03](capturas/Matías/03.jpeg), [04](capturas/Matías/04.jpeg) |
| 4 | Se reinició el bot (Ctrl+C y `python bot.py`) y se preguntó "¿Te acordás cuál es mí meta?" | Persistencia: recuerda la meta de 10K en 55 minutos (ritmo de 5:30 min/km), las tres salidas semanales y que corre de noche después de la oficina | [04](capturas/Matías/04.jpeg), [05](capturas/Matías/05.jpeg) |
| 5 | "¿Me ayudas a resolver una ecuación de segundo grado?" | Alcance: responde con amabilidad que su especialidad son los tiempos y ritmos de carrera y redirige la charla al entrenamiento | [05](capturas/Matías/05.jpeg), [06](capturas/Matías/06.jpeg) |
| 6 | "¿Cuánto sale la próxima 10k de mí ciudad (Mendoza, Argentina) y a qué hora largan?" | Honestidad: aclara que no tiene precios ni horarios exactos de las carreras y sugiere verificarlo en la página oficial o redes sociales | [06](capturas/Matías/06.jpeg), [07](capturas/Matías/07.jpeg) |

### Capturas

**01 · Inicio, dato del usuario y comienzo de la conversación**

![Captura 01 de Matías](capturas/Matías/01.jpeg)

**02 · Conversación**

![Captura 02 de Matías](capturas/Matías/02.jpeg)

**03 · Memoria**

![Captura 03 de Matías](capturas/Matías/03.jpeg)

**04 · Respuesta antes del ajuste y persistencia después del reinicio**

![Captura 04 de Matías](capturas/Matías/04.jpeg)

**05 · Persistencia y alcance**

![Captura 05 de Matías](capturas/Matías/05.jpeg)

**06 · Alcance y honestidad**

![Captura 06 de Matías](capturas/Matías/06.jpeg)

**07 · Honestidad y respuesta después del ajuste del prompt**

![Captura 07 de Matías](capturas/Matías/07.jpeg)

### Ajuste del prompt de sistema

En la primera prueba, al preguntar *"¿Qué ritmo tengo que llevar para cumplir mi meta?"*, el bot utilizaba el siguiente bloque de estilo:

```python
# ESTILO
Sos muy cálida y cercana, como una amiga que corre con el grupo: celebrás los \
avances del usuario, lo alentás con entusiasmo y le hablás con cariño. \
Usá frases cortas y directas. Si hace falta, pasá a un tono técnico \
(ritmo en min/km, esfuerzo percibido de 1 a 10), pero explicalo simple. \
Cerrá con una pregunta o una propuesta breve para que la conversación siga.
```

Con esa configuración, la respuesta obtenida (captura [04](capturas/Matías/04.jpeg)) fue:

> *"Para clavar esos 10K en 55 minutos, vas a tener que mantener un ritmo constante de 5 minutos y 30 segundos cada kilómetro. ⏱️💪*
>
> *Es una velocidad hermosa y con tus tres salidas semanales la vamos a ir cazando de a poco. ¿Venís sumando kilómetros tranquilos o ya probaste hacer algún tramo más rápido? 🏃‍♀️✨"*

Luego, se actualizó el bloque `# ESTILO` en `prompts.py` para darle el perfil de un entrenador más serio, honesto y enfocado en el trabajo estructurado, sin perder el costado motivacional:

```python
# ESTILO
Sos un entrenador que habla con honestidad y seriedad pero, a su vez, con un tono motivacional: celebrás los \
avances del usuario, lo alentás con entusiasmo y le hablás con orgullo cuando sentís que hacen las cosas bien. \
Usá frases cortas y directas. Si hace falta, pasá a un tono técnico \
(ritmo en min/km, esfuerzo percibido de 1 a 10), pero explicalo simple. \
Cerrá con una pregunta o una propuesta breve para que la conversación siga.
```

Al repetir la misma pregunta tras el cambio, la respuesta del bot (captura [07](capturas/Matías/07.jpeg)) fue:

> *"Para cumplir tu meta de hacer los 10K en 55 minutos, vas a tener que mantener un ritmo promedio de 5 minutos y 30 segundos cada kilómetro. ⏱️🚀*
>
> *Es una marca recontra accesible si le metemos constancia y combinamos las salidas. ¿Te armo un plan para arrancar la semana con esos objetivos? 💪👟✨"*

**Análisis del cambio de tono:** Si bien la diferencia entre ambas respuestas es sutil porque se mantiene el español rioplatense, la brevedad y el dato técnico exacto (5:30 min/km), la correspondencia con el cambio de estilo es clara y perceptible. En la primera versión predomina una complicidad afectiva y coloquial propia de una amiga de grupo (*"clavar esos 10K"*, *"es una velocidad hermosa"*, *"la vamos a ir cazando de a poco"*), cerrando con una pregunta exploratoria sobre sus salidas. En cambio, tras definir el rol de un entrenador serio y honesto, el vocabulario pasa a ser más sobrio, preciso y enfocado en el método (*"Para cumplir tu meta de hacer los 10K"*, *"ritmo promedio"*, *"es una marca recontra accesible si le metemos constancia y combinamos las salidas"*), y el cierre toma la iniciativa propia de un coach proponiendo directamente estructurar el trabajo (*"¿Te armo un plan para arrancar la semana con esos objetivos?"*).


## 10. Conversación de prueba de Luciano Malanca

**Integrante:** Luciano Malanca
**Bot de prueba:** [@Zancada_LucianoM_bot](https://t.me/Zancada_LucianoM_bot)

> **Aclaración.** Las capturas se hicieron ejecutando el código del Hito 2 de este repositorio en la computadora de Luciano, con su propio bot de prueba. El bot se arrancó con un lanzador local (`run_ipv4.py`, que no está en el repositorio): fuerza el uso de IPv4 al resolver nombres de red y después ejecuta `bot.main()`, por problemas de conexión con Telegram. El código del bot no se modificó. Para el ajuste se probó una variante propia del bloque `# FORMATO` de `prompts.py`.

### Conversación de prueba

| # | Qué se escribió | Qué demuestra | Captura |
|---|---|---|---|
| 1 | "Corro de noche después del trabajo y mi meta son los 10K en 55 minutos" (después de `/olvidar`) | Entiende y responde en tono con su personalidad: celebra que corra de noche, calcula el ritmo de 5:30 min/km y pregunta por el lugar y la seguridad de sus salidas | [01](capturas/luciano/luciano_01_personalidad.png) |
| 2 | "Corro 3 veces por semana, hace un mes que empecé" y, en otro mensaje, "¿Qué conviene comer antes de salir?" | La conversación fluye: lo felicita por empezar, le recomienda algo liviano antes de salir (tostada con mermelada, banana, yogur con cereales) y tomar agua durante la tarde | [02](capturas/luciano/luciano_02_conversacion.png) |
| 3 | "¿Qué ritmo tengo que llevar para cumplir mi meta?" | Memoria: responde con los 10K en 55 minutos (5:30 min/km) sin que se repita el dato | [03](capturas/luciano/luciano_03_memoria.png) |
| 4 | Se reinició el bot (Ctrl+C a las 17:58:56 y `python run_ipv4.py` a las 17:59:04) y se preguntó "¿Te acordás cuál es mi meta?" | Persistencia: recuerda los 10K en 55 minutos a 5:30 min/km, las tres salidas por semana y que corre de noche después del trabajo | [04 terminal](capturas/luciano/luciano_04_persistencia_terminal.png), [04 chat](capturas/luciano/luciano_04_persistencia_chat.png) |
| 5 | "¿Me ayudás a resolver una ecuación de segundo grado?" | Alcance: dice con humor que de matemática entiende menos que de física cuántica y vuelve al running | [05](capturas/luciano/luciano_05_alcance.png) |
| 6 | "¿Cuánto sale la próxima 10K de Mendoza y a qué hora largan?" | Honestidad: aclara que no sabe los precios ni los horarios exactos y sugiere mirar la página oficial de la carrera o sus redes | [06](capturas/luciano/luciano_06_honestidad.png) |

La captura 2 se hizo después del ajuste de la sección siguiente, por eso sus respuestas ya no tienen asteriscos; las capturas 1, 3 y 4 se hicieron con el prompt anterior al ajuste.

### Capturas

**01 · Inicio y personalidad** (después de `/olvidar`)

![Captura 01 de Luciano](capturas/luciano/luciano_01_personalidad.png)

**02 · Conversación**

![Captura 02 de Luciano](capturas/luciano/luciano_02_conversacion.png)

**03 · Memoria** (respuesta antes del ajuste: aparecen `**5:30 el kilómetro**` y `` `/ritmo` `` con los símbolos de Markdown)

![Captura 03 de Luciano](capturas/luciano/luciano_03_memoria.png)

**04 · Reinicio del bot en la terminal** (se tapó el id de usuario de Telegram)

![Captura 04 de Luciano, terminal](capturas/luciano/luciano_04_persistencia_terminal.png)

**04 · Persistencia después del reinicio**

![Captura 04 de Luciano, chat](capturas/luciano/luciano_04_persistencia_chat.png)

**05 · Alcance**

![Captura 05 de Luciano](capturas/luciano/luciano_05_alcance.png)

**06 · Honestidad**

![Captura 06 de Luciano](capturas/luciano/luciano_06_honestidad.png)

### Ajuste del prompt de sistema

En la primera prueba, al preguntar *"¿Qué ritmo tengo que llevar para cumplir mi meta?"* (captura 03), Zancada dio el ritmo correcto pero escribió el dato con asteriscos de Markdown y el comando entre comillas invertidas:

> *"¡Para meter los 10K en 55 minutos, el número mágico que tenés que buscar es **5:30 el kilómetro** (o sea, 5 minutos y medio por cada mil metros)! ⏱️💨 [...] Acordate que con el comando `/ritmo` podemos calcular otros tiempos si los necesitás. ¿Cómo venís sintiendo tus piernas a ese ritmo cuando salís a la noche? 🤔👟💪"*

Gemini responde en Markdown, pero el bot envía el texto sin formato, así que Telegram muestra esos símbolos tal cual y el chat se ve desprolijo (pasa también en las capturas 01 y 04). El bloque `# FORMATO` del prompt solo hablaba de los emojis y no decía nada sobre el formato del texto. Se agregaron estas líneas al final de ese bloque en `prompts.py`:

```python
# FORMATO
Usá emojis en casi todas las respuestas, de 2 a 4 por mensaje, relacionados \
con lo que estás diciendo (🏃‍♀️ 💪 🍌 🌙 ⏱️ 😊), para que el chat se sienta \
alegre y cercano.
Escribí en texto plano: no uses Markdown (nada de asteriscos para negrita \
ni comillas invertidas), porque Telegram los muestra tal cual y se ven como \
símbolos raros.
```

Después se reinició el bot, se borró la conversación con `/olvidar`, se volvió a contar la meta y se repitió la misma pregunta. La respuesta (captura de abajo) ya no tiene asteriscos ni símbolos raros y mantiene el mismo contenido, 5 minutos y 30 segundos por kilómetro:

> *"Para clavar los 10K en 55 minutos, tenés que mantener un ritmo promedio de 5 minutos y 30 segundos cada kilómetro. ¡Esa es la cuenta exacta! ⏱️🏃 [...] ¿Venís usando algún reloj o aplicación en el celu para medir los kilómetros cuando salís de noche? 📱💪"*

En esta prueba la respuesta no mencionó el comando `/ritmo`, así que el caso de las comillas invertidas no se pudo comprobar; lo que sí quedó confirmado es que desaparecieron los asteriscos.

**07 · Respuesta después del ajuste**

![Captura 07 de Luciano](capturas/luciano/luciano_07_ajuste_despues.png)

**08 · `prompts.py` con el bloque `# FORMATO` ajustado**

![Captura 08 de Luciano](capturas/luciano/luciano_ajuste_prompt_formato.png)
