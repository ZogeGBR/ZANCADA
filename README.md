# Zancada · coach de running en Telegram (TIF)

Bot de Telegram que conversa con Gemini con la personalidad de un coach de running, recuerda la conversación aunque se reinicie, consulta el clima real, registra entrenamientos y arma planes.

📄 **Informe del TIF:** [`docs/INFORME_TIF.md`](docs/INFORME_TIF.md) · **Pendientes:** [`docs/PENDIENTES.md`](docs/PENDIENTES.md)

📄 **Informe del Hito 2:** [`docs/INFORME_HITO2.md`](docs/INFORME_HITO2.md) (prompt de sistema, conversación de prueba con capturas y ajuste del prompt).

## Qué hace

| Entrada | Respuesta |
|---|---|
| `/start`, `/help` | Saludo y lista de comandos |
| `/ritmo 10 52:30` | Ritmo, velocidad y tiempos estimados (fórmula de Riegel) |
| `/registrar hoy corrí 8 km en 44 min` | Extrae distancia/tiempo/tipo con salida estructurada (JSON validado con Pydantic) y pide confirmación con botones |
| Foto de un reloj o app | Gemini multimodal lee la captura y propone registrar el entrenamiento |
| `/resumen` | Totales y detalle de los últimos 7 días (SQLite) |
| `/plan` | Flujo guiado (distancia → semanas → días) y plan generado por Gemini |
| `/olvidar` · `/borrar_entrenos` | Borra la conversación · borra los entrenamientos guardados |
| Cualquier texto | Gemini conversa y, si hace falta, **usa herramientas** (function calling): clima de hoy y mejores horas (Open-Meteo), calcular ritmo, registrar entrenamiento, resumir la semana |

## Cómo funciona la memoria

El modelo no recuerda nada entre consultas. En cada mensaje, `bot.py`:

1. lee los últimos 20 mensajes del usuario desde SQLite (`db.py` (aiosqlite)),
2. los envía a Gemini junto con el prompt de sistema (`prompts.py`) y el mensaje nuevo,
   usando la Interactions API con `store=False` (`llm.py`),
3. guarda el mensaje y la respuesta en SQLite.

## Function calling (resumen)

Gemini no ejecuta nada: responde "quiero llamar a `clima_para_correr(ciudad=…)`", el bot ejecuta la función real (`tools.py`) y le devuelve el resultado; se repite (máx. 4 rondas) hasta que responde con texto. Como `store=False`, en cada ronda se reenvían los pasos anteriores. El `user_id` lo pone el bot, nunca el modelo.

## Archivos

- `bot.py`: handlers de Telegram, flujo `/plan` y arranque.
- `dominio.py`: lógica pura (ritmo, Riegel, tiempos).
- `tools.py`: herramientas que invoca Gemini (clima Open-Meteo, ritmo, registrar, resumir).
- `schemas.py`: esquema Pydantic del entrenamiento (extracción estructurada).
- `tests/test_integracion.py`: pruebas de punta a punta con Telegram/Gemini/Open-Meteo simulados (`python -I tests/test_integracion.py`).
- `prompts.py`: prompt de sistema (identidad, tarea y alcance, estilo, formato, honestidad).
- `llm.py`: consulta a Gemini.
- `db.py` (aiosqlite): historial y entrenamientos en SQLite.
- `docs/`: informe del Hito 2 y capturas de la conversación de prueba.
- `.env.example`: variables necesarias. **El `.env` y el `.db` no se suben al repositorio.**

## Puesta en marcha

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
```

Completá en `.env`:

```
TELEGRAM_TOKEN=...   # de @BotFather
GEMINI_API_KEY=...   # de Google AI Studio
GEMINI_MODEL=gemini-3.5-flash-lite
```

Y corré `python bot.py`. Se crea `zancada.db` solo la primera vez.

## Problemas comunes

| Síntoma | Causa probable |
|---|---|
| Al arrancar: "Faltan variables en el .env" | Falta `TELEGRAM_TOKEN` o `GEMINI_API_KEY` |
| "Tuve un problema para pensar la respuesta" | Modelo inexistente (404), falla de red o del servicio: mirá el error en la consola |
| "Tengo un problema de configuración" | Clave inválida (401 o 403): copiala de nuevo desde AI Studio |
| "Estoy recibiendo demasiadas consultas" | Cuota del plan gratuito superada (429): esperá y reintentá |
| El bot olvidó todo | Se borró `zancada.db` o se usó `/olvidar` |
| `Conflict: terminated by other getUpdates` | Hay dos copias del bot corriendo con el mismo token |

## Créditos y límites

Clima: [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0; uso no comercial). Las predicciones de tiempos y los planes son orientativos; Zancada no da consejos médicos.
