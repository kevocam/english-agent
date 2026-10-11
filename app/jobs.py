"""Tareas programadas. Un 'tick' cada minuto revisa qué toca enviar.

Así cambiar horarios en la tabla `settings` funciona sin reiniciar nada.
"""

import asyncio
import logging

from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes

from app import config, db, practice, schedule
from app.bot import messages

log = logging.getLogger(__name__)


async def _send(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    await context.bot.send_message(
        chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, link_preview_options=messages.NO_PREVIEW
    )


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

        chat_id = settings["telegram_chat_id"]
        await _send(context, chat_id, messages.format_morning(items, now.toordinal()))
        await asyncio.to_thread(db.mark_morning_sent, session["id"])
        context.bot_data["morning_sent_date"] = now.date()
        log.info("Mensaje de la mañana enviado (%s items)", len(items))
    except Exception:
        log.exception("morning_tick falló; se reintenta en el próximo minuto")
        return

    # Primer ejercicio de la cadena (si falla, /hoy lo reintenta)
    if config.ANTHROPIC_API_KEY:
        try:
            for text in await practice.start(session, items):
                await _send(context, chat_id, text)
        except Exception:
            log.exception("No se pudo arrancar la práctica de la mañana")


async def nudge_tick(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Insistencia: si hay un ejercicio pendiente sin respuesta, recordarlo (10 → 20 → 40 min)."""
    try:
        settings = await asyncio.to_thread(db.get_settings)
        if settings.get("telegram_chat_id") is None:
            return
        now = schedule.local_now(settings)
        if schedule.is_quiet(settings, now):
            return
        session = await asyncio.to_thread(db.get_today_session, settings)
        if not session or not schedule.nudge_due(settings, now, session):
            return

        count = session.get("nudge_count") or 0
        await _send(context, settings["telegram_chat_id"], messages.format_nudge(session["current_exercise"], count))
        await asyncio.to_thread(db.mark_nudged, session["id"], count + 1)
        log.info("Recordatorio #%s enviado", count + 1)
    except Exception:
        log.exception("nudge_tick falló; se reintenta en el próximo minuto")


def register_jobs(app: Application) -> None:
    app.job_queue.run_repeating(morning_tick, interval=60, first=5, name="morning")
    app.job_queue.run_repeating(nudge_tick, interval=60, first=35, name="nudge")
