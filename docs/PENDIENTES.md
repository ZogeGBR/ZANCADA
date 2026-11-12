# Pendientes del TIF

Lista de lo que falta antes de la defensa. Marcá cada ítem cuando esté hecho.

## Imprescindible (antes de presentar)

- [ ] **Probar con las claves reales** (nada de esto se pudo probar en vivo):
  - [ ] Preguntar "¿cómo está el clima para correr hoy en Mendoza?" (function calling + Open-Meteo)
  - [ ] `/registrar hoy corrí 8 km en 44 minutos` y confirmar con el botón
  - [ ] Mandar la foto de un reloj o app y confirmar
  - [ ] `/resumen`
  - [ ] `/plan` completo (10K, 8 semanas, 4 días)
  - [ ] Si Gemini rechaza la llamada con herramientas o con imagen, corregir `llm.py` (el formato salió del SDK, no de una prueba real)
- [ ] **Completar el equipo**: nombre, integrantes y roles en `docs/INFORME_TIF.md`, en el informe online y en la portada y el cierre de las diapositivas
- [ ] **Confirmar con el profesor** los requisitos del TIF (no hay rúbrica oficial; se armaron con las clases 1 y 2 y los hitos)
- [ ] **Sacar capturas** de las pruebas reales y agregarlas a `docs/capturas/` (clima, registro por texto, foto, resumen, plan)
- [ ] **Ensayar la demo** de 3 minutos y tener capturas de respaldo por si falla internet
- [ ] **Compartir** el informe y las diapositivas con el equipo (menú Compartir) y dar acceso al profesor al repositorio si es privado

## Recomendado

- [ ] Decidir si se restaura en `prompts.py` la regla de formato (texto plano, 2 a 5 líneas) que se perdió al ajustar el estilo
- [ ] Que cada integrante corra el bot en su máquina (ver la guía del equipo) para poder defender cualquier parte
- [ ] Repartir quién explica cada diapositiva (hay notas de orador en cada una)
- [ ] Revisar que `.env` y `zancada.db` no estén en el repositorio
- [ ] Hacer merge de la rama `tif` a `main` cuando esté todo probado (hoy `main` conserva la entrega del Hito 2)
- [ ] Exportar el informe a PDF si el profesor lo pide en ese formato

## Opcional (mejoras si sobra tiempo)

- [ ] Evaluación sistemática: 10 preguntas fijas con criterios de calidad (módulo de evaluación)
- [ ] Pronóstico de varios días y recordatorios de entrenamiento
- [ ] Servidor permanente y webhooks en lugar de polling
- [ ] Gráficos de progreso semanal
