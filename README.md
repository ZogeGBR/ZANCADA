# Zancada · coach de running en Telegram (v3)

Bot de Telegram que conversa con Gemini con la personalidad de un coach de running,
y recuerda la conversación aunque se reinicie.

📄 **Informe del Hito 2:** [`docs/INFORME_HITO2.md`](docs/INFORME_HITO2.md) (prompt de sistema, conversación de prueba con capturas y ajuste del prompt).

## Qué hace

| Entrada | Respuesta |
|---|---|
| `/start` | Saludo personalizado |
| `/help` | Lista de comandos |
| `/ritmo 10 52:30` | Ritmo, velocidad y tiempos estimados (fórmula de Riegel) |
| `/olvidar` | Borra el historial de la conversación del usuario |
| Cualquier texto | Respuesta de Gemini (Interactions API sin estado) |
| Foto, audio, sticker | Aviso de que por ahora solo entiende texto |

## Cómo funciona la memoria

El modelo no recuerda nada entre consultas. En cada mensaje, `bot.py`:

1. lee los últimos 20 mensajes del usuario desde SQLite (`db.py` (aiosqlite)),
2. los envía a Gemini junto con el prompt de sistema (`prompts.py`) y el mensaje nuevo,
   usando la Interactions API con `store=False` (`llm.py`),
3. guarda el mensaje y la respuesta en SQLite.

## Archivos

- `bot.py`: handlers de Telegram y arranque.
- `prompts.py`: prompt de sistema (identidad, tarea y alcance, estilo, formato, honestidad).
- `llm.py`: consulta a Gemini.
- `db.py` (aiosqlite): historial en SQLite.
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

## Hoja de ruta

v1 comandos · v3 Gemini + SQLite · v4 function calling (clima con Open-Meteo y registro de entrenamientos) · v5 salida estructurada · v6 flujo guiado · v7 módulo avanzado.
