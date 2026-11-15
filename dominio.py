"""Lógica del dominio de Zancada (sin Telegram ni Gemini): se puede probar sola.

La usan el comando /ritmo y las herramientas que Gemini invoca (function calling).
"""

import math

DISTANCIAS_CLASICAS = {"5K": 5.0, "10K": 10.0, "21K": 21.0975, "42K": 42.195}


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
