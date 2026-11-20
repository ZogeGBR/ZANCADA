# Zancada · Hitos 3 y 4: entrega

**Materia:** Sistemas Inteligentes Aplicados 2026 · ITU UNCUYO · Prof. Ing. Miguel Pérez Díaz  
**Integrantes:** Zoe Garcia Badiola, Ignacio Morichetti Ramal, Matias Lopez, Gonzalo Laspada y Luciano Malanca  
**Repositorio:** https://github.com/ZogeGBR/zancada (rama `main`)  
**Video (Hitos 3 y 4):** https://drive.google.com/file/d/1M38wIBaSUkUb34a8bdIBAFhjeFuuhU-4/view?usp=sharing  

## Hito 3 · Obligatorios parciales · Estado de avance

Zancada es un bot de Telegram que actúa como coach de running con Gemini. Los obligatorios ya funcionan:

- **Gemini con personalidad:** responde como coach de running (rol, tono y reglas en `prompts.py`) y deriva con amabilidad lo que no tiene que ver con correr.
- **Memoria:** el historial de cada usuario se guarda en SQLite y se reenvía a Gemini en cada consulta (`store=False`), así que la conversación continúa incluso después de reiniciar el bot.
- **Reinicio y borrado:** `/start` presenta el bot y `/olvidar` borra el historial del usuario.
- **Función propia:** Gemini llama herramientas con function calling (`clima_para_correr` con Open-Meteo, `calcular_ritmo`); la terminal muestra cada llamada y su resultado.
- **Errores y claves:** los errores 429, 401, 403 y 5xx se traducen a avisos amables; las claves están solo en `.env`, que no se sube al repositorio.

**Pendiente:** ningún obligatorio.

## Hito 4 · Módulos avanzados · Estado de avance

- **Salida estructurada:** `/registrar hoy corrí 8 km en 44 min` pide a Gemini un JSON con esquema (`km`, `minutos`, `tipo`, `notas`), lo valida con Pydantic, pide confirmación con botones y lo guarda en SQLite. Los datos absurdos o fuera de esquema se rechazan.
- **Multimodalidad:** el bot acepta fotos (con o sin leyenda) y notas de voz. Una captura de reloj se lee y se propone como entrenamiento; una nota de voz se escucha y se responde en el contexto del bot. Foto y audio quedan en el historial, por lo que el mensaje siguiente continúa la conversación.
- **Flujo guiado:** `/plan` pregunta distancia, semanas y días por semana, valida cada dato (por ejemplo, 9 días se rechaza), muestra un resumen con botones Armar plan o Cancelar y recién al confirmar genera el plan. `/cancelar` permite salir a mitad del flujo.

Las 52 pruebas de integración pasan (`python tests/test_integracion.py`). **Limitaciones:** la lectura de fotos depende de su legibilidad y las notas de voz se limitan a 2 minutos.
