"""Memoria de Zancada: historial de conversación en SQLite (Hito 2 · v3).

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
