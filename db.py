"""Memoria de Zancada en SQLite: historial de conversación y registro de entrenamientos (TIF).

Cada mensaje (del usuario o del modelo) es una fila de la tabla `mensajes`.
Se usa aiosqlite, la versión asíncrona de sqlite3, para que las operaciones
sobre la base no bloqueen al bot mientras atiende a otros usuarios.
El archivo .db guarda conversaciones de personas reales: NO se sube a GitHub.
"""

import aiosqlite  # SQLite con soporte para async/await

# Se crea en la carpeta desde la que se ejecuta el bot (la raíz del proyecto).
# Ejecutá siempre `python bot.py` desde esa carpeta; si no, se crea otra base.
RUTA_DB = "zancada.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS mensajes (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,                  -- orden de llegada
    user_id INTEGER NOT NULL,                                   -- id de Telegram: separa a cada usuario
    rol     TEXT    NOT NULL CHECK (rol IN ('user', 'model')),  -- quién escribió
    texto   TEXT    NOT NULL,                                   -- contenido del mensaje
    fecha   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP          -- cuándo se guardó
);
CREATE INDEX IF NOT EXISTS idx_mensajes_usuario ON mensajes (user_id, id);

CREATE TABLE IF NOT EXISTS entrenamientos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fecha   TEXT    NOT NULL DEFAULT (date('now')),             -- día del entrenamiento (AAAA-MM-DD)
    km      REAL    NOT NULL CHECK (km > 0),
    minutos REAL    NOT NULL CHECK (minutos > 0),
    tipo    TEXT    NOT NULL DEFAULT 'rodaje',                  -- rodaje, series, fondo, carrera...
    notas   TEXT
);
CREATE INDEX IF NOT EXISTS idx_entrenos_usuario ON entrenamientos (user_id, fecha);
"""


async def inicializar() -> None:
    """Crea la tabla y el índice si todavía no existen (se llama al arrancar)."""
    async with aiosqlite.connect(RUTA_DB) as db:
        await db.executescript(ESQUEMA)
        await db.commit()


async def guardar_intercambio(user_id: int, pregunta: str, respuesta: str) -> None:
    """Guarda en una sola operación el mensaje del usuario y la respuesta del modelo."""
    async with aiosqlite.connect(RUTA_DB) as db:
        # Los ? son parámetros: SQLite inserta los valores de forma segura (evita inyección SQL).
        await db.executemany(
            "INSERT INTO mensajes (user_id, rol, texto) VALUES (?, ?, ?)",
            [(user_id, "user", pregunta), (user_id, "model", respuesta)],
        )
        await db.commit()


async def obtener_historial(user_id: int, limite: int) -> list[tuple[str, str]]:
    """Últimos `limite` mensajes del usuario, del más antiguo al más reciente."""
    async with aiosqlite.connect(RUTA_DB) as db:
        cursor = await db.execute(
            "SELECT rol, texto FROM mensajes WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limite),
        )
        filas = await cursor.fetchall()
    # La consulta trae del más reciente al más antiguo; se invierte para que
    # el modelo lea la conversación en orden cronológico.
    historial = [(rol, texto) for rol, texto in reversed(filas)]
    # Gemini espera turnos alternados que empiecen por el usuario.
    while historial and historial[0][0] != "user":
        historial.pop(0)
    return historial


async def borrar_historial(user_id: int) -> int:
    """Borra la conversación de un usuario y devuelve cuántos mensajes eliminó."""
    async with aiosqlite.connect(RUTA_DB) as db:
        cursor = await db.execute("DELETE FROM mensajes WHERE user_id = ?", (user_id,))
        await db.commit()
        return cursor.rowcount


async def guardar_entrenamiento(user_id: int, km: float, minutos: float,
                                tipo: str = "rodaje", notas: str | None = None,
                                fecha: str | None = None) -> int:
    """Registra un entrenamiento y devuelve su id. `fecha` (AAAA-MM-DD) por defecto es hoy."""
    async with aiosqlite.connect(RUTA_DB) as db:
        cursor = await db.execute(
            "INSERT INTO entrenamientos (user_id, km, minutos, tipo, notas, fecha) "
            "VALUES (?, ?, ?, ?, ?, COALESCE(?, date('now')))",
            (user_id, km, minutos, tipo, notas, fecha),
        )
        await db.commit()
        return cursor.lastrowid


async def resumen_entrenamientos(user_id: int, dias: int = 7) -> dict:
    """Totales de los últimos `dias` días (incluido hoy) y el detalle de cada salida."""
    async with aiosqlite.connect(RUTA_DB) as db:
        cursor = await db.execute(
            "SELECT fecha, km, minutos, tipo, notas FROM entrenamientos "
            "WHERE user_id = ? AND fecha >= date('now', ?) ORDER BY fecha, id",
            (user_id, f"-{int(dias) - 1} days"),
        )
        filas = await cursor.fetchall()
    km = sum(f[1] for f in filas)
    minutos = sum(f[2] for f in filas)
    return {
        "dias": dias,
        "salidas": len(filas),
        "km_totales": round(km, 2),
        "minutos_totales": round(minutos, 1),
        "ritmo_promedio_min_km": round(minutos / km, 2) if km else None,
        "detalle": [{"fecha": f[0], "km": f[1], "minutos": f[2], "tipo": f[3], "notas": f[4]} for f in filas],
    }


async def borrar_entrenamientos(user_id: int) -> int:
    """Borra los entrenamientos de un usuario (lo usa /olvidar junto con el historial)."""
    async with aiosqlite.connect(RUTA_DB) as db:
        cursor = await db.execute("DELETE FROM entrenamientos WHERE user_id = ?", (user_id,))
        await db.commit()
        return cursor.rowcount
