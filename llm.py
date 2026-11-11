"""Conexión con Gemini mediante la Interactions API, en modo SIN ESTADO (Hito 2 · v2/v3).

store=False: Google no guarda la conversación. En cada consulta se envían el
prompt de sistema, el historial (leído de SQLite) y el mensaje nuevo.
La clave y el modelo se leen del .env; nunca van escritos en el código.
"""

import logging
import os

from dotenv import load_dotenv
from google import genai

from prompts import PROMPT_SISTEMA

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Leer el modelo del .env permite cambiarlo sin tocar el código.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

logger = logging.getLogger("zancada.llm")

# Un único cliente para todo el programa (administra las conexiones HTTP).
cliente_gemini = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


class ErrorGemini(Exception):
    """Falla al consultar a Gemini. `codigo` es el status HTTP si lo hubo (429, 401, 403...)."""

    def __init__(self, mensaje: str, codigo: int | None = None):
        super().__init__(mensaje)
        self.codigo = codigo


def armar_entrada(historial: list[tuple[str, str]], mensaje_nuevo: str) -> list[dict]:
    """Convierte el historial guardado en la lista de pasos (steps) de la Interactions API
    y agrega al final el mensaje nuevo del usuario."""
    tipo_de_paso = {"user": "user_input", "model": "model_output"}
    pasos = [
        {"type": tipo_de_paso[rol], "content": [{"type": "text", "text": texto}]}
        for rol, texto in historial
    ]
    pasos.append({"type": "user_input", "content": [{"type": "text", "text": mensaje_nuevo}]})
    return pasos


async def consultar_gemini(historial: list[tuple[str, str]], mensaje: str) -> str:
    """Envía a Gemini la conversación completa y devuelve el texto de la respuesta."""
    try:
        # .aio es la versión asíncrona del cliente: mientras Gemini piensa,
        # el bot puede atender a otros usuarios.
        interaccion = await cliente_gemini.aio.interactions.create(
            model=GEMINI_MODEL,
            system_instruction=PROMPT_SISTEMA,
            input=armar_entrada(historial, mensaje),
            store=False,  # la memoria la administra el bot, no Google
        )
    except Exception as exc:
        logger.error("Error al consultar a Gemini: %s", exc)
        raise ErrorGemini(str(exc), getattr(exc, "status_code", None)) from exc
    return interaccion.output_text or "No se me ocurrió nada para responder 🤔"
