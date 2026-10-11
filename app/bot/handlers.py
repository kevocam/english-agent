import asyncio

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from app import config, db
from app.bot import messages


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
    _, items = await asyncio.to_thread(db.get_or_create_today_session, settings)
    await update.effective_message.reply_text(messages.format_today(items), parse_mode=ParseMode.HTML)


def build_application() -> Application:
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["hoy", "today"], today))
    return app
