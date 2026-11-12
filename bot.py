"""
Zancada · tu coach de running en Telegram (Trabajo Integrador Final).

Qué hace esta versión:
  /start   -> saludo personalizado
  /help    -> lista de comandos
  /ritmo   -> calcula ritmo y predice tiempos (comando propio del dominio)
  /olvidar -> borra el historial de la conversación con este usuario
  /registrar <texto> -> extrae un entrenamiento de un texto libre (salida estructurada)
  /resumen -> tus entrenamientos de los últimos 7 días
  /plan    -> flujo guiado: arma un plan de entrenamiento con Gemini
  foto     -> lee una captura de tu reloj/app y propone registrar el entrenamiento
  texto    -> conversa con Gemini (Interactions API sin estado) que puede usar
              herramientas (clima, ritmo, registrar, resumir); memoria en SQLite
  errores  -> se registran en consola y el usuario recibe un aviso amable

Se ejecuta con:  python bot.py   (con el entorno virtual activado)
"""

import logging
import os
import warnings

from dotenv import load_dotenv
from telegram.warnings import PTBUserWarning
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import db
import llm
from dominio import calcular_ritmo, formatear_minutos, parsear_tiempo
from llm import ErrorGemini, consultar_gemini, extraer_entrenamiento

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
# Aviso informativo de PTB sobre per_message: nuestro flujo /plan funciona bien así.
warnings.filterwarnings("ignore", message=".*per_message.*", category=PTBUserWarning)
# httpx registra cada petición a Telegram en nivel INFO: lo bajamos para que
# la consola no se llene de ruido (y para no imprimir la URL con el token).
logging.getLogger("httpx").setLevel(logging.WARNING)

TEXTO_AYUDA = (
    "Esto es lo que puedo hacer:\n\n"
    "/start - Presentación\n"
    "/help - Esta ayuda\n"
    "/ritmo <km> <tiempo> - Calculo tu ritmo y te estimo otras distancias\n"
    "    Ejemplo: /ritmo 10 52:30\n"
    "/registrar <texto> - Guardo un entrenamiento\n"
    "    Ejemplo: /registrar hoy corrí 8 km en 44 minutos\n"
    "/resumen - Tus entrenamientos de la última semana\n"
    "/plan - Armamos juntos un plan de entrenamiento\n"
    "/olvidar - Borro nuestra conversación y empezamos de cero\n"
    "/borrar_entrenos - Borro todos tus entrenamientos guardados\n\n"
    "También podés mandarme una foto de tu reloj o app 📸, preguntarme por el clima "
    "para salir a correr o escribirme lo que quieras sobre running. "
    "Me acuerdo de lo que me contás, incluso si me reinician."
)

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
        respuesta = await consultar_gemini(historial, texto, user_id)
    except ErrorGemini as error:
        # Si la consulta falló no se guarda nada: el historial nunca queda con una pregunta sin respuesta.
        await mensaje.reply_text(describir_error(error))
        return
    # Paso 3: guardar la pregunta y la respuesta para la próxima consulta.
    await db.guardar_intercambio(user_id, texto, respuesta)
    # Si la respuesta supera el límite de Telegram, se envía en partes.
    for inicio in range(0, len(respuesta), LIMITE_TELEGRAM):
        await mensaje.reply_text(respuesta[inicio:inicio + LIMITE_TELEGRAM])


# ---------------------------------------------------------------------------
# TIF · Entrenamientos: extracción estructurada, fotos y confirmación
# ---------------------------------------------------------------------------
def teclado_confirmacion() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ Guardar", callback_data="entreno:si"),
                                  InlineKeyboardButton("❌ Descartar", callback_data="entreno:no")]])


async def proponer_entrenamiento(update: Update, context: ContextTypes.DEFAULT_TYPE, **fuente) -> None:
    """Extrae un entrenamiento (de texto o imagen) y pide confirmación antes de guardarlo."""
    mensaje = update.effective_message
    await mensaje.chat.send_action(ChatAction.TYPING)
    try:
        entreno = await extraer_entrenamiento(**fuente)
    except ErrorGemini as error:
        await mensaje.reply_text(describir_error(error))
        return
    if entreno is None:
        await mensaje.reply_text(
            "No pude sacar distancia y tiempo de eso 🤔. Probá con algo como: "
            "/registrar hoy corrí 8 km en 44 minutos"
        )
        return
    context.user_data["pendiente"] = entreno.model_dump()
    await mensaje.reply_text(
        f"Entendí esto 👇\n📏 {entreno.km:g} km en {formatear_minutos(entreno.minutos)} "
        f"({formatear_minutos(entreno.minutos / entreno.km)} min/km)\n🏷️ {entreno.tipo}"
        + (f"\n📝 {entreno.notas}" if entreno.notas else "") + "\n\n¿Lo guardo?",
        reply_markup=teclado_confirmacion(),
    )


async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/registrar <texto libre>."""
    texto = " ".join(context.args).strip()
    if not texto:
        await update.message.reply_text("Contame qué corriste 🏃‍♀️. Ej: /registrar hoy corrí 8 km en 44 minutos")
        return
    await proponer_entrenamiento(update, context, texto=texto)


async def foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foto de un reloj/app: Gemini (multimodal) lee los datos y se pide confirmación."""
    mensaje = update.effective_message
    archivo = await mensaje.photo[-1].get_file()  # la de mayor resolución
    datos = bytes(await archivo.download_as_bytearray())
    await proponer_entrenamiento(update, context, texto=mensaje.caption, imagen=(datos, "image/jpeg"))


async def confirmar_entrenamiento(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Botones ✅/❌ del entrenamiento propuesto."""
    consulta = update.callback_query
    await consulta.answer()
    pendiente = context.user_data.pop("pendiente", None)
    if consulta.data == "entreno:no" or not pendiente:
        await consulta.edit_message_text("Descartado 👍" if pendiente else "Ese registro ya no está disponible.")
        return
    await db.guardar_entrenamiento(update.effective_user.id, pendiente["km"], pendiente["minutos"],
                                   pendiente["tipo"], pendiente["notas"])
    await consulta.edit_message_text("¡Guardado! 💪 Ya lo ves en /resumen.")


async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/resumen: últimos 7 días, calculado directamente desde SQLite."""
    r = await db.resumen_entrenamientos(update.effective_user.id, 7)
    if not r["salidas"]:
        await update.message.reply_text("Todavía no tenés entrenamientos esta semana. Registrá uno con /registrar 🏃")
        return
    lineas = [f"📅 Últimos 7 días: {r['salidas']} salidas · {r['km_totales']:g} km · "
              f"{formatear_minutos(r['minutos_totales'])} · ritmo medio {formatear_minutos(r['ritmo_promedio_min_km'])} min/km", ""]
    lineas += [f"• {d['fecha']}: {d['km']:g} km en {formatear_minutos(d['minutos'])} ({d['tipo']})" for d in r["detalle"]]
    await update.message.reply_text("\n".join(lineas))


async def borrar_entrenos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    n = await db.borrar_entrenamientos(update.effective_user.id)
    await update.message.reply_text(f"Borré {n} entrenamientos 🗑️.")


# ---------------------------------------------------------------------------
# TIF · /plan: flujo guiado con ConversationHandler (distancia -> semanas -> días)
# ---------------------------------------------------------------------------
PLAN_DISTANCIA, PLAN_SEMANAS, PLAN_DIAS = range(3)


async def plan_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("plan", None)
    botones = [[InlineKeyboardButton(d, callback_data=f"plan:{d}") for d in ("5K", "10K", "21K", "42K")]]
    await update.message.reply_text("¡Armemos tu plan! 🗓️ ¿Para qué distancia te preparás? (/cancelar para salir)",
                                    reply_markup=InlineKeyboardMarkup(botones))
    return PLAN_DISTANCIA


async def plan_distancia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    consulta = update.callback_query
    await consulta.answer()
    context.user_data["plan"] = {"distancia": consulta.data.split(":", 1)[1]}
    await consulta.edit_message_text(f"Genial, {context.user_data['plan']['distancia']} 💪")
    await consulta.message.reply_text("¿En cuántas semanas es tu objetivo? (entre 2 y 24)")
    return PLAN_SEMANAS


async def _numero(update: Update, minimo: int, maximo: int) -> int | None:
    texto = (update.message.text or "").strip()
    if texto.isdigit() and minimo <= int(texto) <= maximo:
        return int(texto)
    await update.message.reply_text(f"Necesito un número entre {minimo} y {maximo} 🙂")
    return None


async def plan_semanas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    n = await _numero(update, 2, 24)
    if n is None:
        return PLAN_SEMANAS
    context.user_data["plan"]["semanas"] = n
    await update.message.reply_text("¿Cuántos días por semana podés entrenar? (entre 2 y 6)")
    return PLAN_DIAS


async def plan_dias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    n = await _numero(update, 2, 6)
    if n is None:
        return PLAN_DIAS
    datos = context.user_data.pop("plan")
    datos["dias"] = n
    user_id = update.effective_user.id
    await update.message.chat.send_action(ChatAction.TYPING)
    pedido = (f"Armame un plan de entrenamiento para {datos['distancia']} en {datos['semanas']} semanas, "
              f"entrenando {datos['dias']} días por semana. Resumilo por semana, con progresión gradual y "
              "descanso. Tené en cuenta lo que ya sepas de mí. Cerrá recordando que es orientativo.")
    historial = await db.obtener_historial(user_id, MAX_MENSAJES_HISTORIAL)
    try:
        respuesta = await consultar_gemini(historial, pedido, user_id)
    except ErrorGemini as error:
        await update.message.reply_text(describir_error(error))
        return ConversationHandler.END
    await db.guardar_intercambio(user_id, pedido, respuesta)
    for inicio in range(0, len(respuesta), LIMITE_TELEGRAM):
        await update.message.reply_text(respuesta[inicio:inicio + LIMITE_TELEGRAM])
    return ConversationHandler.END


async def plan_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("plan", None)
    await update.message.reply_text("Plan cancelado. Cuando quieras, /plan de nuevo 🙂")
    return ConversationHandler.END


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
        "Solo entiendo texto y fotos de entrenamientos 🙂. Contame con palabras o probá /ritmo 10 52:30."
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
    app.add_handler(CommandHandler("registrar", registrar, filters=filters.UpdateType.MESSAGE))
    app.add_handler(CommandHandler("resumen", resumen, filters=filters.UpdateType.MESSAGE))
    app.add_handler(CommandHandler("borrar_entrenos", borrar_entrenos, filters=filters.UpdateType.MESSAGE))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("plan", plan_inicio, filters=filters.UpdateType.MESSAGE)],
        states={
            PLAN_DISTANCIA: [CallbackQueryHandler(plan_distancia, pattern=r"^plan:")],
            PLAN_SEMANAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_semanas)],
            PLAN_DIAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, plan_dias)],
        },
        fallbacks=[CommandHandler("cancelar", plan_cancelar)],
    ))
    app.add_handler(CallbackQueryHandler(confirmar_entrenamiento, pattern=r"^entreno:"))
    app.add_handler(MessageHandler(filters.PHOTO & filters.UpdateType.MESSAGE, foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE, responder))
    app.add_handler(MessageHandler(filters.COMMAND & filters.UpdateType.MESSAGE, comando_desconocido))
    app.add_handler(MessageHandler(~filters.TEXT & ~filters.COMMAND & filters.UpdateType.MESSAGE, no_texto))  # va último
    app.add_error_handler(manejar_error)

    logger.info("Zancada en línea con el modelo %s.", llm.GEMINI_MODEL)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
