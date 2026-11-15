# TIF · Zancada: coach de running con IA

Sistemas Inteligentes Aplicados 2026 · ITU UNCUYO · 12/11/2026
Equipo: (completar nombre del equipo e integrantes)

## 1. Resumen y problema que resuelve

**Zancada es un bot de Telegram que actúa como coach de running: calcula ritmos, consulta el clima real para elegir el mejor horario de salida, registra entrenamientos y arma planes, recordando a cada corredor entre conversaciones.**

Los corredores amateurs entrenan sin entrenador: improvisan ritmos, no registran lo que hacen y deciden la salida sin mirar el clima. Las apps de entrenamiento suelen ser rígidas o de pago, y un chat genérico con un LLM no recuerda al usuario ni accede a datos reales. Zancada combina un modelo de lenguaje (Gemini) con herramientas propias, una base de datos y un flujo guiado, en el canal que el corredor ya usa todos los días.

El proyecto evolucionó en tres hitos: v1 (comandos), Hito 2 (Gemini sin estado + memoria en SQLite) y TIF (function calling, salida estructurada, multimodalidad y flujo guiado). Informe del Hito 2: [INFORME_HITO2.md](INFORME_HITO2.md).

## 2. Objetivos y alcance

**Objetivo general:** diseñar, implementar y defender un sistema inteligente real que un corredor pueda usar desde Telegram sin instalar nada.

Objetivos específicos:

- Conversar con una personalidad estable (prompt de sistema) y recordar al usuario aunque el bot se reinicie.
- Resolver con datos reales lo que un LLM no puede saber: el clima de hoy (Open-Meteo) y los entrenamientos del propio usuario.
- Convertir texto libre y fotos de relojes en datos estructurados y validados, siempre con confirmación del usuario antes de guardar.
- Guiar al usuario en un flujo de varios pasos para armar un plan de entrenamiento.
- Fallar con elegancia: cuota agotada, clave inválida, API externa caída o respuestas malformadas no rompen la conversación.

**Fuera de alcance:** diagnósticos o consejos médicos, pronósticos de más de un día, integración con relojes GPS, pagos y despliegue en un servidor permanente (hoy corre en la máquina del equipo con `python bot.py`).

## 3. Arquitectura y decisiones de diseño

```
Corredor (Telegram) <-> bot.py <-> llm.py <-> Gemini (Interactions API)
                          |           |
                          |           +-> tools.py -> Open-Meteo (clima)
                          |                   |
                          +------------> SQLite (db.py): mensajes, entrenamientos
```

El bot es el único que habla con Telegram, la base y las APIs: Gemini solo pide ejecutar herramientas y recibe sus resultados. Decisiones clave:

- Gemini se usa **sin estado** (`store=False`) y el historial vive en SQLite, para controlar el contexto y poder borrarlo.
- La lógica de dominio (`dominio.py`) no depende de Telegram ni de Gemini, así que se prueba sola.
- Todo dato que Gemini devuelve se valida antes de guardarse.

## 4. Cumplimiento de los requisitos de la materia

Zancada cubre los seis requisitos obligatorios y dos módulos avanzados. Los requisitos se tomaron de las clases 1 y 2 y de los hitos; no hay rúbrica oficial del TIF, por lo que conviene validarlos con el profesor.

| Requisito | Cómo lo cumple Zancada | Dónde |
| --- | --- | --- |
| 1. Comandos de Telegram | `/start`, `/help`, `/ritmo`, `/registrar`, `/resumen`, `/plan`, `/cancelar`, `/olvidar`, `/borrar_entrenos` | `bot.py` |
| 2. Gemini con prompt de sistema | Identidad, alcance, estilo, formato y honestidad; se envía en cada consulta | `prompts.py`, `llm.py` |
| 3. Historial en SQLite | Tabla `mensajes` (20 mensajes por consulta, sobrevive reinicios) y tabla `entrenamientos` | `db.py` |
| 4. Function calling (>= 2 funciones, 1 API externa) | `clima_para_correr` (Open-Meteo), `calcular_ritmo`, `registrar_entrenamiento`, `resumen_entrenamientos` | `tools.py` |
| 5. Análisis estructurado | Extracción de entrenamientos a JSON con esquema, validado con Pydantic | `schemas.py`, `llm.py` |
| 6. Manejo de errores y `.env` | Errores 429/401/403/5xx traducidos, herramientas que nunca lanzan, tope de rondas, claves solo en `.env` | `llm.py`, `bot.py` |
| Módulo: multimodalidad | Foto de un reloj o app: Gemini lee distancia y tiempo | `bot.py` (`foto`) |
| Módulo: flujo guiado | `/plan` con `ConversationHandler`: distancia, semanas, días, plan | `bot.py` (`plan_*`) |

No se implementaron RAG, webhooks ni evaluación formal de respuestas del modelo; las pruebas automatizadas validan el comportamiento del bot, no la calidad del texto que genera Gemini.

## 5. Implementación

**Function calling.** Gemini no ejecuta código: devuelve un paso `function_call` con el nombre y los argumentos, el bot corre la función real y responde con un paso `function_result`. El ciclo se repite hasta que el modelo contesta con texto, con un máximo de 4 rondas. Como la API se usa con `store=False`, en cada ronda se reenvían los pasos previos, incluidos los `thought` con su firma. Las herramientas devuelven siempre un diccionario; si algo falla, devuelven `{"error": ...}` y Gemini se lo explica al usuario.

**Clima.** `clima_para_correr` geocodifica la ciudad y pide a Open-Meteo temperatura, probabilidad de lluvia y viento por hora. Puntúa cada hora entre las 5 y las 22 (menor es mejor: distancia a 12 °C + lluvia/10 + viento/5) y devuelve las tres mejores. Es una heurística propia, no un criterio médico.

**Salida estructurada.** `/registrar` y las fotos piden a Gemini un JSON con el esquema `Entrenamiento` (`km`, `minutos`, `tipo`, `notas`, `entendido`). Pydantic valida la respuesta y el bot la rechaza si no hay distancia y tiempo razonables (0 < km <= 1000, 0 < min <= 1440). Antes de guardar, el usuario confirma con botones; un doble clic no duplica el registro.

**Multimodalidad.** La foto de mayor resolución se descarga, se codifica en base64 y se envía junto con la consigna de extracción. Pasa por la misma validación y confirmación que el texto.

**Flujo guiado.** `/plan` usa un `ConversationHandler` con tres estados. Cada paso valida la entrada (semanas entre 2 y 24, días entre 2 y 6), `/cancelar` sale del flujo y, al final, Gemini genera el plan usando el historial del usuario.

**Seguridad de diseño.** El `user_id` lo inyecta el bot al ejecutar cada herramienta: nunca forma parte del esquema que ve el modelo, por lo que un usuario no puede pedirle datos de otra persona.

## 6. Pruebas y evaluación

**42 pruebas de integración pasan** (`tests/test_integracion.py`), más las 27 del Hito 2 que siguen pasando sobre la versión final. Ejecutan el código real de `python-telegram-bot`, el SDK real de `google-genai` y SQLite real; solo se simulan las respuestas HTTP de Gemini, Open-Meteo y Telegram.

| Área | Qué se verifica |
| --- | --- |
| Function calling | La ronda 2 reenvía `user_input`, `thought` (con su firma), `function_call` y `function_result`; `store=False` en todas las rondas; un bucle de herramientas se corta con un mensaje amable |
| Herramientas | El clima elige 3 horas entre 5 y 22 h; ciudad inexistente, Open-Meteo caído, argumentos inválidos, herramienta desconocida y distancia absurda devuelven un error en vez de romper |
| Datos | Registrar y resumir leen y escriben SQLite; los entrenamientos de cada usuario están aislados |
| Extracción y confirmación | Texto válido, texto que no es un entrenamiento, km negativo y JSON fuera de esquema; Guardar, Descartar y doble clic |
| Foto | La imagen viaja en base64 a Gemini y propone un registro con botones |
| `/plan` | Entradas inválidas se repreguntan, el plan se genera y `/cancelar` devuelve el chat a la conversación normal |
| Errores y memoria | 429, 403, 500 y respuesta vacía; el historial sobrevive a un reinicio y `/olvidar` lo borra |

**Lo que todavía no se probó en vivo:** las llamadas reales a Gemini con herramientas y con imágenes, y las reales a Open-Meteo, no estaban accesibles desde el entorno donde se desarrolló el código. El formato de los pasos de function calling se tomó del SDK instalado (`google-genai` 3.2.0). Antes de la defensa hay que repetir cinco pruebas manuales con las claves reales: clima de Mendoza, registrar por texto, registrar por foto, `/resumen` y `/plan`.

## 7. Seguridad, privacidad y limitaciones

**Seguridad y privacidad.**

- Las claves (`TELEGRAM_TOKEN`, `GEMINI_API_KEY`) viven en `.env`, que no se sube a GitHub; el repositorio incluye solo `.env.example`.
- `zancada.db` guarda conversaciones y entrenamientos de personas reales y tampoco se sube.
- El usuario puede borrar su conversación (`/olvidar`) y sus entrenamientos (`/borrar_entrenos`).
- El prompt prohíbe diagnosticar, recetar y pedir datos personales o sensibles.
- Open-Meteo es gratuita para uso no comercial y exige atribución (CC BY 4.0); se cita en el README y en la respuesta de la herramienta.
- Al usar Gemini, el texto y las fotos que el usuario envía viajan a Google; conviene avisarlo a quienes prueben el bot.

**Limitaciones conocidas.**

- El clima es solo el de hoy.
- Los planes y las predicciones (fórmula de Riegel, válida entre distancias parecidas) son orientativos.
- La extracción desde fotos depende de la legibilidad de la captura; por eso siempre hay confirmación.
- El bot funciona mientras `python bot.py` esté corriendo en la máquina de alguien del equipo.
- Las pruebas automatizadas simulan a Gemini: no miden la calidad ni la veracidad de sus respuestas.

## 8. Trabajo en equipo, conclusiones y trabajo futuro

| Integrante | Rol | Aporte |
| --- | --- | --- |
| Zoe Garcia Badiola | (completar) | Repositorio, Hitos 1 y 2, prompt de sistema, pruebas con el bot real |
| (completar) | (completar) | (completar) |

**Conclusiones.** Un LLM solo conversa; lo que lo vuelve útil es lo que lo rodea: memoria propia, herramientas que consultan datos reales, validación de lo que devuelve y un usuario que confirma antes de guardar. Con `store=False` el control del contexto queda en el bot, lo que facilita la privacidad (`/olvidar` borra de verdad) a cambio de reenviar el historial en cada consulta.

**Trabajo futuro:** evaluación sistemática con preguntas y criterios fijos; recordatorios y pronóstico de varios días; despliegue en un servidor con webhooks; gráficos de progreso semanal.
