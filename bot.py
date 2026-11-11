"""
Zancada v3 · tu coach de running en Telegram, ahora con Gemini.

Qué hace esta versión (Clase 2):
  /start   -> saludo personalizado
  /help    -> lista de comandos
  /ritmo   -> calcula ritmo y predice tiempos (comando propio del dominio)
  /olvidar -> borra el historial de la conversación con este usuario
  texto    -> conversa con Gemini (Interactions API sin estado), con la
              personalidad definida en prompts.py y memoria en SQLite
  errores  -> se registran en consola y el usuario recibe un aviso amable

Se ejecuta con:  python bot.py   (con el entorno virtual activado)
"""

import logging
import math
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db
import llm
from llm import ErrorGemini, consultar_gemini

# ---------------------------------------------------------------------------
# Etapa 1 · Leer el token desde .env (nunca escrito en el código)
# ---------------------------------------------------------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("zancada")
# httpx registra cada petición a Telegram en nivel INFO: lo bajamos para que
# la consola no se llene de ruido (y para no imprimir la URL con el token).
logging.getLogger("httpx").setLevel(logging.WARNING)

TEXTO_AYUDA = (
    "Esto es lo que puedo hacer:\n\n"
    "/start - Presentación\n"
    "/help - Esta ayuda\n"
    "/ritmo <km> <tiempo> - Calculo tu ritmo y te estimo otras distancias\n"
    "    Ejemplo: /ritmo 10 52:30\n"
    "/olvidar - Borro nuestra conversación y empezamos de cero\n\n"
    "También podés escribirme lo que quieras sobre running y te respondo. "
    "Me acuerdo de lo que me contás, incluso si me reinician."
)

DISTANCIAS_CLASICAS = {"5K": 5.0, "10K": 10.0, "21K": 21.0975, "42K": 42.195}


# ---------------------------------------------------------------------------
# Lógica del dominio (funciones comunes, sin Telegram).
# Se pueden probar solas y en la Clase 3 Gemini las va a invocar.
# ---------------------------------------------------------------------------
def parsear_tiempo(texto: str) -> float:
    """Convierte '45', '45:30' o '1:05:00' en minutos (float)."""
    partes = texto.strip().split(":")
    if not 1 <= len(partes) <= 3 or not all(p.isdigit() for p in partes):
        raise ValueError(f"Tiempo inválido: {texto!r}")
    numeros = [int(p) for p in partes]
    if len(numeros) == 1:            # '45'      -> 45 minutos
        horas, minutos, segundos = 0, numeros[0], 0
    elif len(numeros) == 2:          # '45:30'   -> 45 min 30 s
        horas, (minutos, segundos) = 0, numeros
    else:                            # '1:05:00' -> 1 h 5 min
        horas, minutos, segundos = numeros
        if minutos >= 60:
            raise ValueError(f"Tiempo inválido: {texto!r}")
    if segundos >= 60:
        raise ValueError(f"Tiempo inválido: {texto!r}")
    total = horas * 60 + minutos + segundos / 60
    if total <= 0:
        raise ValueError("El tiempo tiene que ser mayor a cero")
    return total


def formatear_minutos(minutos: float) -> str:
    """45.5 -> '45:30'; 125.0 -> '2:05:00'."""
    total_seg = round(minutos * 60)
    h, resto = divmod(total_seg, 3600)
    m, s = divmod(resto, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def calcular_ritmo(distancia_km: float, minutos: float) -> dict:
    """Ritmo (min/km), velocidad (km/h) y predicción de Riegel: T2 = T1 * (D2/D1)^1.06."""
    if not (math.isfinite(distancia_km) and math.isfinite(minutos)):
        raise ValueError("Valores no finitos")
    if not (0 < distancia_km <= 1000 and 0 < minutos <= 24 * 60):
        raise ValueError("Distancia (hasta 1000 km) y tiempo (hasta 24 h) fuera de rango")
    predicciones = {
        nombre: formatear_minutos(minutos * (km / distancia_km) ** 1.06)
        for nombre, km in DISTANCIAS_CLASICAS.items()
    }
    return {
        "ritmo_min_km": formatear_minutos(minutos / distancia_km),
        "velocidad_kmh": round(distancia_km / (minutos / 60), 2),
        "predicciones": predicciones,
    }


# ---------------------------------------------------------------------------
# Etapas 2 a 4 · Handlers (cada uno es una corrutina: async def + await)
# ---------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /start."""
    nombre = update.effective_user.first_name
    logger.info("Nuevo /start de %s (id %s)", nombre, update.effective_user.id)
    await update.message.reply_text(
        f"¡Hola, {nombre}! 🏃 Soy Zancada, tu coach de running.\n\n"
        "Te ayudo a calcular ritmos, elegir el mejor horario para salir a correr "
        "y llevar el registro de tus entrenamientos.\n\n"
        "Probá con /ritmo 10 52:30 o escribí /help para ver todo lo que sé hacer."
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /help."""
    await update.message.reply_text(TEXTO_AYUDA)


async def ritmo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ritmo <km> <tiempo>. context.args trae las palabras que siguen al comando."""
    uso = "Usalo así: /ritmo <km> <tiempo>\nEjemplos: /ritmo 5 25  ·  /ritmo 21.1 1:52:00"
    if len(context.args) != 2:
        await update.message.reply_text(uso)
        return
    try:
        distancia = float(context.args[0].replace(",", "."))
        minutos = parsear_tiempo(context.args[1])
        resultado = calcular_ritmo(distancia, minutos)
    except ValueError:
        # Error esperable (el usuario escribió mal): se le explica, no se cae el bot.
        await update.message.reply_text("No pude entender esos datos. " + uso)
        return

    lineas = [
        f"📏 {distancia:g} km en {formatear_minutos(minutos)}",
        f"⏱️ Ritmo: {resultado['ritmo_min_km']} min/km",
        f"🚀 Velocidad: {resultado['velocidad_kmh']} km/h",
        "",
        "Con ese nivel podrías hacer aproximadamente:",
    ]
    lineas += [f"  • {nombre}: {t}" for nombre, t in resultado["predicciones"].items()]
    lineas.append("\n(Estimación de Riegel: más confiable entre distancias parecidas.)")
    await update.message.reply_text("\n".join(lineas))


LIMITE_TELEGRAM = 4096  # longitud máxima de un mensaje de Telegram, en caracteres
# Mensajes anteriores que se envían al modelo en cada consulta (20 = 10 preguntas y respuestas).
# Más memoria = más lento y más cuota consumida por consulta.
MAX_MENSAJES_HISTORIAL = 20


def describir_error(error: Exception) -> str:
    """Traduce un error de la API a un mensaje comprensible para el usuario."""
    codigo = getattr(error, "codigo", None)
    if codigo == 429:  # se superó la cuota de consultas
        return "Estoy recibiendo demasiadas consultas ⏳. Probá de nuevo en un minuto, por favor."
    if codigo in (401, 403):  # clave inválida o sin permiso
        return "Tengo un problema de configuración 🔧. Avisale a quien me administra."
    return "Tuve un problema para pensar la respuesta 🙏. ¿Me lo preguntás de nuevo?"


async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde con Gemini, teniendo en cuenta la conversación previa (texto que NO es comando)."""
    mensaje = update.effective_message
    user_id = update.effective_user.id
    texto = (mensaje.text or "").strip()
    if not texto:
        return
    logger.info("Mensaje de %s: %s", user_id, texto)
    await mensaje.chat.send_action(ChatAction.TYPING)

    # Paso 1: recuperar lo que ya se habló con este usuario.
    historial = await db.obtener_historial(user_id, MAX_MENSAJES_HISTORIAL)
    # Paso 2: consultar al modelo con el historial más el mensaje nuevo.
    try:
        respuesta = await consultar_gemini(historial, texto)
    except ErrorGemini as error:
        # Si la consulta falló no se guarda nada: el historial nunca queda con una pregunta sin respuesta.
        await mensaje.reply_text(describir_error(error))
        return
    # Paso 3: guardar la pregunta y la respuesta para la próxima consulta.
    await db.guardar_intercambio(user_id, texto, respuesta)
    # Si la respuesta supera el límite de Telegram, se envía en partes.
    for inicio in range(0, len(respuesta), LIMITE_TELEGRAM):
        await mensaje.reply_text(respuesta[inicio:inicio + LIMITE_TELEGRAM])


async def olvidar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/olvidar: borra el historial de este usuario."""
    borrados = await db.borrar_historial(update.effective_user.id)
    logger.info("Usuario %s borró %d mensajes", update.effective_user.id, borrados)
    await update.effective_message.reply_text("Listo, empezamos de cero. ¿En qué te ayudo? 🙂")


async def comando_desconocido(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cualquier /comando que no registramos (ignora los dirigidos a otro bot, ej. /start@OtroBot)."""
    primera = (update.effective_message.text or "").split()[0]
    if "@" in primera and primera.split("@", 1)[1].lower() != (context.bot.username or "").lower():
        return
    await update.message.reply_text("No conozco ese comando 🤔. Escribí /help para ver la lista.")


async def no_texto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fotos, audios, stickers, etc.: por ahora solo se entiende texto."""
    await update.effective_message.reply_text(
        "Por ahora solo entiendo texto 🙂. Contame con palabras o probá /ritmo 10 52:30."
    )


# ---------------------------------------------------------------------------
# Etapa 5 · Manejo de errores
# ---------------------------------------------------------------------------
async def manejar_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Se llama cuando un handler lanza una excepción no controlada."""
    logger.error("Error procesando un update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Uy, me tropecé 😅. Ya quedó registrado el problema; probá de nuevo en un rato."
        )


async def al_iniciar(app: Application) -> None:
    """Se ejecuta una sola vez, antes de recibir mensajes (db.inicializar necesita await)."""
    await db.inicializar()
    logger.info("Base de datos lista (%s).", db.RUTA_DB)


def main() -> None:
    faltantes = [
        nombre
        for nombre, valor in [("TELEGRAM_TOKEN", TELEGRAM_TOKEN), ("GEMINI_API_KEY", llm.GEMINI_API_KEY)]
        if not valor
    ]
    if faltantes:
        raise SystemExit(
            f"Faltan variables en el .env: {', '.join(faltantes)}. "
            "Copiá .env.example como .env y completalo."
        )

    app = Application.builder().token(TELEGRAM_TOKEN).post_init(al_iniciar).build()

    # El orden importa: la Application entrega el update al primer handler que lo acepta.
    # filters.UpdateType.MESSAGE ignora los mensajes editados (llegan sin update.message).
    app.add_handler(CommandHandler("start", start, filters=filters.UpdateType.MESSAGE))
    app.add_handler(CommandHandler("help", ayuda, filters=filters.UpdateType.MESSAGE))
    app.add_handler(CommandHandler("ritmo", ritmo, filters=filters.UpdateType.MESSAGE))
    app.add_handler(CommandHandler("olvidar", olvidar, filters=filters.UpdateType.MESSAGE))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE, responder))
    app.add_handler(MessageHandler(filters.COMMAND & filters.UpdateType.MESSAGE, comando_desconocido))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE, no_texto))  # va último
    app.add_error_handler(manejar_error)

    logger.info("Zancada v3 en línea con el modelo %s.", llm.GEMINI_MODEL)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
