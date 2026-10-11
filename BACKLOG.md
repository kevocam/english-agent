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
- [ ] Deploy en Railway (webhook)

## MVP (siguientes sprints)
- [ ] H3 · Ejercicios en contexto de trabajo (oración, hueco, traducción, conector, deducción)
- [ ] H4 · Corrección con Claude + score 0–5
- [ ] H5 · Insistencia escalonada si no respondo
- [ ] H6 · Repaso espaciado SM-2 (calificación → próxima fecha)
- [ ] H7 · Gramática dentro del repaso
- [ ] H8 · Mar/jue: calentamiento 15:30 + check post-clase 17:05
- [ ] H9 · Comandos de config: `/pausa`, `/horario`
- [ ] H10 · Cápsulas cada 3 h
- [ ] H11 · Cierre del día 21:00 (racha, aciertos, errores, qué toca mañana)

## Post-MVP
- [ ] Front con progreso (lee Supabase)
- [ ] Audio / speaking
- [ ] Cargar palabras nuevas de cada clase desde Telegram
