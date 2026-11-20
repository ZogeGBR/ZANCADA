# Hitos 3 y 4 - Zancada

Sistemas Inteligentes Aplicados 2026 - ITU UNCUYO
Profesor: Ing. Miguel Pérez Díaz

Integrantes: Zoe Garcia Badiola, Ignacio Morichetti Ramal, Matias Lopez, Gonzalo Laspada y Luciano Malanca

Repositorio: https://github.com/ZogeGBR/zancada (rama main)

Video de los Hitos 3 y 4: https://drive.google.com/file/d/1M38wIBaSUkUb34a8bdIBAFhjeFuuhU-4/view?usp=sharing

## Estado de avance del Hito 3

Zancada es un bot de Telegram que funciona como coach de running y usa Gemini. Los puntos obligatorios del hito ya están funcionando. El bot responde con una personalidad definida en el prompt de sistema (tono cercano, voseo y frases cortas) y guarda el historial de cada usuario en SQLite, así que recuerda la conversación aunque se reinicie. Con /start se presenta y con /olvidar se borra lo guardado. Como función propia, Gemini puede pedirle al bot que consulte el clima en Open-Meteo para recomendar horarios o que calcule un ritmo, y en la terminal se ve cada llamada con su resultado. Los errores de la API (cuota, clave inválida, servidor caído) se traducen a mensajes claros y las claves están en un archivo .env que no se sube al repositorio.

Todo lo obligatorio está resuelto, no nos queda nada pendiente de este hito.

## Estado de avance del Hito 4

Sumamos los tres módulos avanzados.

Para la salida estructurada, el comando /registrar toma un texto como "hoy corrí 8 km en 44 minutos" y le pide a Gemini un JSON con distancia, tiempo, tipo de entrenamiento y notas. Ese JSON se valida con Pydantic, el usuario lo confirma con botones y recién ahí se guarda en la base de datos. Si los datos no tienen sentido, no se guardan.

En multimodalidad, el bot entiende fotos y notas de voz. Si la foto es la captura de un reloj, propone registrar el entrenamiento; si no, la comenta como parte de la conversación. Las notas de voz las escucha Gemini y las responde en el mismo chat. La foto y el audio quedan en el historial, por eso un mensaje posterior sigue la conversación con ese contexto.

El flujo guiado es el comando /plan. Pregunta la distancia, las semanas y los días por semana, y rechaza los datos inválidos (por ejemplo, 9 días por semana). Al final muestra un resumen para confirmar o cancelar, y solo si se confirma Gemini arma el plan. Con /cancelar se puede salir en cualquier momento.

Las 52 pruebas automáticas pasan (python tests/test_integracion.py). Como limitaciones, la lectura de fotos depende de que la captura se vea bien y las notas de voz están limitadas a 2 minutos.
