"""Conexión con Gemini mediante la Interactions API, en modo SIN ESTADO (Hito 2 + TIF).

store=False: Google no guarda la conversación. En cada consulta se envían el
prompt de sistema, el historial (leído de SQLite) y el mensaje nuevo.
La clave y el modelo se leen del .env; nunca van escritos en el código.
"""

import base64
import json
import logging
import os

from dotenv import load_dotenv
from google import genai

from prompts import PROMPT_SISTEMA
from schemas import ESQUEMA_ENTRENAMIENTO, Entrenamiento
from tools import HERRAMIENTAS, ejecutar_herramienta

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


MAX_RONDAS_HERRAMIENTAS = 4  # tope de vueltas modelo -> herramienta -> modelo (evita bucles)


async def _crear(**kwargs):
    """Una llamada a la Interactions API; unifica los errores en ErrorGemini."""
    try:
        return await cliente_gemini.aio.interactions.create(model=GEMINI_MODEL, store=False, **kwargs)
    except Exception as exc:
        logger.error("Error al consultar a Gemini: %s", exc)
        raise ErrorGemini(str(exc), getattr(exc, "status_code", None)) from exc


async def consultar_gemini(historial: list[tuple[str, str]], mensaje: str,
                           user_id: int | None = None, usar_herramientas: bool = True) -> str:
    """Envía a Gemini la conversación y devuelve el texto final.

    Si el modelo pide ejecutar herramientas (function calling), el bot las corre y le
    devuelve los resultados; se repite hasta que responde con texto. Como no hay estado
    en Google, en cada vuelta se reenvían los pasos anteriores (incluidos los del modelo).
    """
    entrada = armar_entrada(historial, mensaje)
    for _ in range(MAX_RONDAS_HERRAMIENTAS + 1):
        args = {"system_instruction": PROMPT_SISTEMA, "input": entrada}
        if usar_herramientas:
            args["tools"] = HERRAMIENTAS
        interaccion = await _crear(**args)
        llamadas = [p for p in interaccion.steps if p.type == "function_call"]
        if not llamadas:
            return interaccion.output_text or "No se me ocurrió nada para responder 🤔"
        # Se reenvía lo que dijo el modelo (con sus llamadas) y luego el resultado de cada una.
        entrada += [p.model_dump(mode="json", exclude_none=True) for p in interaccion.steps]
        for llamada in llamadas:
            resultado = await ejecutar_herramienta(llamada.name, dict(llamada.arguments or {}), user_id or 0)
            logger.info("Herramienta %s(%s) -> %s", llamada.name, llamada.arguments, resultado)
            entrada.append({"type": "function_result", "call_id": llamada.id, "name": llamada.name,
                            "result": json.dumps(resultado, ensure_ascii=False)})
    raise ErrorGemini("Demasiadas rondas de herramientas sin respuesta final")


async def extraer_entrenamiento(texto: str | None = None,
                                imagen: tuple[bytes, str] | None = None) -> Entrenamiento | None:
    """Extracción estructurada: pasa un texto libre o una captura (bytes, mime) a un Entrenamiento
    validado con Pydantic. Devuelve None si la salida no es JSON válido o no describe un entrenamiento."""
    contenido = [{"type": "text", "text": "Extraé los datos de este entrenamiento de running. "
                  "Si no es un entrenamiento, poné entendido=false. No inventes valores que no figuren."
                  + (f"\n\nTexto del usuario: {texto}" if texto else "")}]
    if imagen:
        datos, mime = imagen
        contenido.append({"type": "image", "data": base64.b64encode(datos).decode(), "mime_type": mime})
    interaccion = await _crear(
        input=[{"type": "user_input", "content": contenido}],
        response_format={"type": "text", "mime_type": "application/json", "schema_": ESQUEMA_ENTRENAMIENTO},
    )
    try:
        entrenamiento = Entrenamiento.model_validate_json(interaccion.output_text or "")
    except ValueError:  # JSON roto o fuera del esquema
        logger.warning("Extracción inválida: %r", interaccion.output_text)
        return None
    return entrenamiento if entrenamiento.es_valido() else None
