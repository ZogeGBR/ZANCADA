# Pendientes del TIF

Lista de lo que falta antes de la defensa. Marcá cada ítem cuando esté hecho.

## Imprescindible (antes de presentar)

- [x] **Probar con las claves reales** (hecho el 15/11; ver InformeEGIfinal) (nada de esto se pudo probar en vivo):
  - [x] Preguntar "¿cómo está el clima para correr hoy en Mendoza?" (function calling + Open-Meteo)
  - [x] `/registrar hoy corrí 8 km en 44 minutos` y confirmar con el botón
  - [x] Mandar la foto de un reloj o app y confirmar
  - [x] Mandar una nota de voz y seguir la conversación después (Hito 4: multimodalidad)
  - [x] `/plan` termina con un resumen y botones Confirmar/Cancelar (Hito 4: flujo guiado)
  - [x] `/resumen`
  - [x] `/plan` completo (10K, 8 semanas, 4 días)
  - [x] Si Gemini rechaza la llamada con herramientas o con imagen, corregir `llm.py` (el formato salió del SDK, no de una prueba real)
- [x] **Completar el equipo**: integrantes cargados en el informe final y las diapositivas (sin roles fijos)
- [ ] **Confirmar con el profesor** los requisitos del TIF (no hay rúbrica oficial; se armaron con las clases 1 y 2 y los hitos)
- [x] **Sacar capturas** de las pruebas reales y agregarlas a `docs/capturas/` (clima, registro por texto, foto, resumen, plan)
- [ ] **Ensayar la demo** de 3 minutos y tener capturas de respaldo por si falla internet
- [ ] **Compartir** el informe y las diapositivas con el equipo (menú Compartir) y dar acceso al profesor al repositorio si es privado

## Recomendado

- [x] Regla de formato restaurada en `prompts.py` (texto plano, respuestas breves) y asteriscos limpiados en `bot.py`
- [ ] Que cada integrante corra el bot en su máquina (ver la guía del equipo) para poder defender cualquier parte
- [ ] Repartir quién explica cada diapositiva (hay notas de orador en cada una)
- [x] Revisar que `.env` y `zancada.db` no estén en el repositorio
- [x] Hacer merge de la rama `tif` a `main` cuando esté todo probado (hoy `main` conserva la entrega del Hito 2)
- [x] Exportar el informe a PDF si el profesor lo pide en ese formato

## Opcional (mejoras si sobra tiempo)

- [ ] Evaluación sistemática: 10 preguntas fijas con criterios de calidad (módulo de evaluación)
- [ ] Pronóstico de varios días y recordatorios de entrenamiento
- [ ] Servidor permanente y webhooks en lugar de polling
- [ ] Gráficos de progreso semanal
