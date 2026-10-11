"""Acceso a Supabase. Funciones síncronas: llamarlas con asyncio.to_thread."""

from datetime import date, datetime, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from supabase import Client, create_client

from app import config
from app.srs import choose_items


@lru_cache
def client() -> Client:
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


# ---------- settings ----------

def get_settings() -> dict:
    return client().table("settings").select("*").eq("id", 1).single().execute().data


def save_chat_id(chat_id: int) -> None:
    client().table("settings").update(
        {"telegram_chat_id": chat_id, "updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", 1).execute()


def today_local(settings: dict) -> date:
    return datetime.now(ZoneInfo(settings["timezone"])).date()


# ---------- sesión del día ----------

def get_or_create_today_session(settings: dict) -> tuple[dict, list[dict]]:
    """Devuelve (sesión, items). Si hoy no hay sesión, elige items y la crea."""
    db = client()
    today = today_local(settings)

    found = db.table("daily_sessions").select("*").eq("session_date", today.isoformat()).execute().data
    if found:
        session = found[0]
    else:
        due = (
            db.table("srs_state")
            .select("item_id, status, due_date, repetitions")
            .lte("due_date", today.isoformat())
            .execute()
            .data
        )
        item_ids = choose_items(due, settings["items_per_day"])
        session = (
            db.table("daily_sessions")
            .insert({"session_date": today.isoformat(), "item_ids": item_ids})
            .execute()
            .data[0]
        )

    if not session["item_ids"]:
        return session, []
    items = db.table("items").select("*").in_("id", session["item_ids"]).execute().data
    order = {item_id: i for i, item_id in enumerate(session["item_ids"])}
    items.sort(key=lambda it: order[it["id"]])
    return session, items
