# Zancada · Hito 3: Obligatorios parciales · Estado de avance

**Integrantes:** Zoe Garcia Badiola, Ignacio Morichetti Ramal, Matias Lopez, Gonzalo Laspada y Luciano Malanca
**Materia:** Sistemas Inteligentes Aplicados 2026 · ITU UNCUYO · Prof. Ing. Miguel Pérez Díaz
**Repositorio:** https://github.com/ZogeGBR/zancada
**Video:** [pegar acá el link del video]

## Estado de avance

Zancada es un bot de Telegram que actúa como coach de running con Gemini. Para este hito ya funcionan los obligatorios:

- **Gemini con personalidad:** el bot responde como coach de running (rol, tono y reglas de formato definidos en `prompts.py`) y rechaza con amabilidad lo que no tiene que ver con correr.
- **Memoria:** el historial de cada usuario se guarda en SQLite y se reenvía a Gemini en cada consulta (modo sin estado, `store=False`), así que la conversación sigue entre mensajes y después de reiniciar el bot.
- **Reinicio y borrado:** `/start` reinicia la bienvenida y `/olvidar` borra de verdad el historial del usuario.
- **Función propia:** Gemini puede llamar a herramientas (function calling) como `calcular_ritmo` y `clima_para_correr` (Open-Meteo); el log de la terminal muestra cada llamada y su resultado.
- **Errores y claves:** los errores 429, 401, 403 y 5xx se traducen a avisos amables y las claves viven solo en `.env`, que no está en el repositorio.

Las 52 pruebas de integración pasan (`python tests/test_integracion.py`) y se probó el bot con claves reales el 15/11.

**Pendiente:** ninguno de los obligatorios. Los módulos avanzados (salida estructurada, multimodalidad y flujo guiado) se entregan en el Hito 4.
