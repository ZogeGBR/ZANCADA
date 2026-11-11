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
