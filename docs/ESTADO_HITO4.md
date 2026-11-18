# Zancada · Hito 4: Módulos avanzados · Estado de avance

**Integrantes:** Zoe Garcia Badiola, Ignacio Morichetti Ramal, Matias Lopez, Gonzalo Laspada y Luciano Malanca
**Materia:** Sistemas Inteligentes Aplicados 2026 · ITU UNCUYO · Prof. Ing. Miguel Pérez Díaz
**Repositorio:** https://github.com/ZogeGBR/zancada
**Video:** [pegar acá el link del video]

## Estado de avance

Sobre la base del Hito 3 se completaron tres módulos avanzados:

- **Salida estructurada:** `/registrar hoy corrí 8 km en 44 min` pide a Gemini un JSON con esquema (`km`, `minutos`, `tipo`, `notas`), lo valida con Pydantic, pide confirmación con botones y recién ahí lo guarda en SQLite. Datos absurdos o fuera de esquema se rechazan.
- **Multimodalidad:** el bot acepta fotos (con o sin leyenda) y notas de voz. Una captura de reloj o app se lee y se propone como entrenamiento; una nota de voz se escucha y se responde en el contexto del bot. Foto y audio quedan en el historial, por lo que el mensaje siguiente continúa la conversación.
- **Flujo guiado:** `/plan` pregunta distancia, semanas y días por semana, valida cada dato (por ejemplo, 9 días se rechaza), muestra un resumen con botones Armar plan o Cancelar y recién al confirmar genera el plan. `/cancelar` permite salir a mitad del flujo.

Las 52 pruebas de integración pasan y cubren estos módulos. La salida estructurada, la foto, el resumen y el plan se probaron con claves reales el 15/11.

**Pendiente:** la nota de voz y la confirmación final de `/plan` se agregaron después de esa prueba real; se verifican en vivo durante la grabación del video. Limitaciones conocidas: la lectura de fotos depende de la legibilidad, y las notas de voz se limitan a 2 minutos.
