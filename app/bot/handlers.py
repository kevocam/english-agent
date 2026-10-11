import asyncio
import logging

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app import config, db, practice, tutor
from app.jobs import register_jobs
from app.bot import messages

log = logging.getLogger(__name__)


async def _owner_settings(update: Update) -> dict | None:
    """Bot de un solo dueño: el primer /start reclama el bot; el resto se ignora."""
    settings = await asyncio.to_thread(db.get_settings)
    chat_id = update.effective_chat.id
    owner = settings.get("telegram_chat_id")

    if owner is None:
        await asyncio.to_thread(db.save_chat_id, chat_id)
        settings["telegram_chat_id"] = chat_id
        return settings
    if owner != chat_id:
        await update.effective_message.reply_text(messages.NOT_OWNER)
        return None
    return settings


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await _owner_settings(update) is None:
        return
    await update.effective_message.reply_text(messages.WELCOME, parse_mode=ParseMode.HTML)


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = await _owner_settings(update)
    if settings is None:
        return
    session, items = await asyncio.to_thread(db.get_or_create_today_session, settings)
    await _send(update, [messages.format_today(items)])
    if config.ANTHROPIC_API_KEY:
        try:
            await _send(update, await practice.start(session, items))
        except Exception:
            log.exception("No se pudo arrancar la práctica")
            await update.effective_message.reply_text(messages.TUTOR_ERROR)


async def _send(update: Update, texts: list[str]) -> None:
    for text in texts:
        await update.effective_message.reply_text(
            text, parse_mode=ParseMode.HTML, link_preview_options=messages.NO_PREVIEW
        )



async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cualquier texto que no sea comando: lo responde el tutor (Claude)."""
    settings = await _owner_settings(update)
    if settings is None:
        return
    if not config.ANTHROPIC_API_KEY:
        await update.effective_message.reply_text(messages.NO_LLM)
        return

    await update.effective_chat.send_action(ChatAction.TYPING)
    text = update.effective_message.text
    try:
        session, items = await asyncio.to_thread(db.get_or_create_today_session, settings)
        if practice.is_pending(session) and items:
            # Hay un ejercicio esperando: Claude decide si es respuesta o pregunta
            await _send(update, await practice.handle_message(session, items, text, settings))
            return
        history = context.chat_data.setdefault("history", [])
        answer = await tutor.reply(history, text, items)
    except Exception:
        log.exception("El tutor falló")
        await update.effective_message.reply_text(messages.TUTOR_ERROR)
        return
    await update.effective_message.reply_text(answer, link_preview_options=messages.NO_PREVIEW)


def build_application() -> Application:
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["hoy", "today"], today))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    register_jobs(app)
    return app
