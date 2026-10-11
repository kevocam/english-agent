"""Tareas programadas. Un 'tick' cada minuto revisa qué toca enviar.

Así cambiar horarios en la tabla `settings` funciona sin reiniciar nada.
"""

import asyncio
import logging

from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes

from app import db, schedule
from app.bot import messages

log = logging.getLogger(__name__)


async def morning_tick(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        settings = await asyncio.to_thread(db.get_settings)
        now = schedule.local_now(settings)
        # Chequeo barato primero, para no consultar sesiones cada minuto
        sent_today = context.bot_data.get("morning_sent_date") == now.date()
        if not schedule.morning_due(settings, now, already_sent=sent_today):
            return

        session, items = await asyncio.to_thread(db.get_or_create_today_session, settings)
        if session.get("morning_sent_at"):  # ya enviado (ej. antes de un reinicio)
            context.bot_data["morning_sent_date"] = now.date()
            return

        await context.bot.send_message(
            chat_id=settings["telegram_chat_id"],
            text=messages.format_morning(items, now.toordinal()),
            parse_mode=ParseMode.HTML,
        )
        await asyncio.to_thread(db.mark_morning_sent, session["id"])
        context.bot_data["morning_sent_date"] = now.date()
        log.info("Mensaje de la mañana enviado (%s items)", len(items))
    except Exception:
        log.exception("morning_tick falló; se reintenta en el próximo minuto")


def register_jobs(app: Application) -> None:
    app.job_queue.run_repeating(morning_tick, interval=60, first=5, name="morning")
