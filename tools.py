"""Herramientas que Gemini puede invocar (function calling) · TIF.

Gemini no ejecuta nada: devuelve "quiero llamar a X con estos argumentos" y el
bot ejecuta la función real y le devuelve el resultado. El user_id NUNCA lo
decide el modelo: lo pone el bot, así un usuario no puede tocar datos ajenos.
"""

import logging
from datetime import date

import httpx

import db
from dominio import calcular_ritmo, formatear_minutos, parsear_tiempo

logger = logging.getLogger("zancada.tools")

URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
URL_PRONOSTICO = "https://api.open-meteo.com/v1/forecast"

# Declaración de las herramientas (JSON Schema) que se le envía a Gemini.
HERRAMIENTAS = [
    {
        "type": "function",
        "name": "clima_para_correr",
        "description": "Pronóstico de HOY en una ciudad y las mejores horas para salir a correr. "
                       "Usala siempre que pregunten por el clima o el mejor horario.",
        "parameters": {
            "type": "object",
            "properties": {"ciudad": {"type": "string", "description": "Ciudad, ej. 'Mendoza'"}},
            "required": ["ciudad"],
        },
    },
    {
        "type": "function",
        "name": "calcular_ritmo",
        "description": "Calcula ritmo (min/km), velocidad y predice tiempos en 5K, 10K, 21K y 42K "
                       "a partir de una distancia y un tiempo.",
        "parameters": {
            "type": "object",
            "properties": {
                "distancia_km": {"type": "number", "description": "Kilómetros recorridos"},
                "tiempo": {"type": "string", "description": "Tiempo en formato '52:30' o '1:05:00'"},
            },
            "required": ["distancia_km", "tiempo"],
        },
    },
    {
        "type": "function",
        "name": "registrar_entrenamiento",
        "description": "Guarda un entrenamiento que el usuario cuenta que hizo.",
        "parameters": {
            "type": "object",
            "properties": {
                "distancia_km": {"type": "number"},
                "tiempo": {"type": "string", "description": "Formato '52:30' o '1:05:00'"},
                "tipo": {"type": "string", "enum": ["rodaje", "series", "fondo", "carrera", "regenerativo", "otro"]},
                "notas": {"type": "string"},
            },
            "required": ["distancia_km", "tiempo"],
        },
    },
    {
        "type": "function",
        "name": "resumen_entrenamientos",
        "description": "Resumen de los entrenamientos registrados del usuario en los últimos N días.",
        "parameters": {
            "type": "object",
            "properties": {"dias": {"type": "integer", "description": "Ventana en días (7 = última semana)"}},
        },
    },
]


async def clima_para_correr(ciudad: str) -> dict:
    """Open-Meteo (gratis, sin clave): geocodifica la ciudad y arma las mejores horas del día."""
    async with httpx.AsyncClient(timeout=10) as http:
        geo = (await http.get(URL_GEOCODING, params={"name": ciudad, "count": 1, "language": "es"})).json()
        if not geo.get("results"):
            return {"error": f"No encontré la ciudad '{ciudad}'"}
        lugar = geo["results"][0]
        pron = (await http.get(URL_PRONOSTICO, params={
            "latitude": lugar["latitude"], "longitude": lugar["longitude"], "timezone": "auto",
            "forecast_days": 1,
            "hourly": "temperature_2m,precipitation_probability,wind_speed_10m",
        })).json()
    h = pron["hourly"]
    horas = []
    for hora_iso, temp, lluvia, viento in zip(h["time"], h["temperature_2m"],
                                              h["precipitation_probability"], h["wind_speed_10m"]):
        hora = int(hora_iso[11:13])
        if not 5 <= hora <= 22 or None in (temp, lluvia, viento):
            continue
        # Puntaje simple: penaliza alejarse de ~12 °C, la lluvia y el viento (menor = mejor).
        puntaje = abs(temp - 12) + lluvia / 10 + viento / 5
        horas.append({"hora": f"{hora:02d}:00", "temperatura_c": temp, "prob_lluvia_pct": lluvia,
                      "viento_kmh": viento, "_p": puntaje})
    mejores = sorted(horas, key=lambda x: x["_p"])[:3]
    for m in mejores:
        m.pop("_p")
    return {"ciudad": f"{lugar['name']}, {lugar.get('country', '')}".strip(", "),
            "fecha": date.today().isoformat(), "mejores_horas": sorted(mejores, key=lambda x: x["hora"]),
            "fuente": "Open-Meteo.com (CC BY 4.0)"}


async def ejecutar_herramienta(nombre: str, args: dict, user_id: int) -> dict:
    """Ejecuta la herramienta pedida por Gemini. Nunca lanza: los errores vuelven como {'error': ...}
    para que el modelo se los explique al usuario en lugar de romper la conversación."""
    try:
        if nombre == "clima_para_correr":
            return await clima_para_correr(str(args["ciudad"]))
        if nombre == "calcular_ritmo":
            return calcular_ritmo(float(args["distancia_km"]), parsear_tiempo(str(args["tiempo"])))
        if nombre == "registrar_entrenamiento":
            km, minutos = float(args["distancia_km"]), parsear_tiempo(str(args["tiempo"]))
            calcular_ritmo(km, minutos)  # valida rangos
            id_ = await db.guardar_entrenamiento(user_id, km, minutos, args.get("tipo") or "rodaje", args.get("notas"))
            return {"guardado": True, "id": id_, "km": km, "tiempo": formatear_minutos(minutos)}
        if nombre == "resumen_entrenamientos":
            dias = max(1, min(int(args.get("dias") or 7), 365))
            return await db.resumen_entrenamientos(user_id, dias)
        return {"error": f"Herramienta desconocida: {nombre}"}
    except (KeyError, ValueError, TypeError) as exc:
        return {"error": f"Argumentos inválidos para {nombre}: {exc}"}
    except Exception as exc:  # red caída, API externa rota, etc.
        logger.error("Falló la herramienta %s: %s", nombre, exc)
        return {"error": f"No pude ejecutar {nombre} ahora mismo"}
