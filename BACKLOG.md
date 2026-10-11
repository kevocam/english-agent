# english-agent · Product Backlog

**Visión:** un agente en Telegram que cada día me da 2–3 palabras/estructuras de mi curso B2
y me persigue hasta que las uso en contexto. Repaso espaciado para no olvidar nada.

## Reglas del producto
- 😴 Silencio de 23:30 a 05:50 · ⏸️ pausa mar/jue 16:00–17:00 (clases)
- 🔔 Insistencia 10 → 20 → 40 min (luego cada 40), **solo para ejercicios pendientes**
- 🧠 Cápsulas cada 3 h (no insisten) · 📅 fines de semana igual que entre semana
- ⚙️ Todo configurable en la tabla `settings`, sin redeploy

## Sprint 1 · "Mi primera palabra llega a Telegram"
- [x] Setup (repo, Supabase, bot en BotFather)
- [x] H1 · Esquema de DB + seed del curso (37 items)
- [x] Bot por polling: `/start` (bot privado) y `/hoy`
- [x] H2 · Mensaje automático a las 6:00 con los items del día
- [x] Deploy en Railway (polling; webhook queda como mejora)

## Sprint 2 · "El bot me hace practicar"
Decisiones PO: ejercicios en cadena · generados en el momento por Claude · 1 reintento si score < 3 ·
Claude detecta si un mensaje es respuesta o pregunta.
- [x] Tutor libre con Claude (mensajes sin ejercicio pendiente)
- [x] H3 · Ejercicios en cadena tras el mensaje de las 6:00 (oración, hueco, traducción, situación, deducción, conector)
- [x] H4 · Calificación 0–5 + corrección + 1 reintento
- [x] H6 · SM-2 (se califica con el primer intento)
- [x] H7 · Gramática dentro del repaso (mismo flujo, ejercicios de deducción/conector)
- [x] H5 · Insistencia 10 → 20 → 40 min (luego cada 40) solo con ejercicio pendiente
- [ ] Webhook en Railway (elimina el error Conflict en deploys)

## MVP (siguientes sprints)
- [ ] H8 · Mar/jue: calentamiento 15:30 + check post-clase 17:05
- [ ] H9 · Comandos de config: `/pausa`, `/horario`
- [ ] H10 · Cápsulas cada 3 h
- [ ] H11 · Cierre del día 21:00 (racha, aciertos, errores, qué toca mañana)

## Post-MVP
- [ ] Front con progreso (lee Supabase)
- [ ] Audio / speaking
- [ ] Cargar palabras nuevas de cada clase desde Telegram
