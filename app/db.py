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
    session = found[0] if found else None

    if session is None or not session["item_ids"]:
        # Los nuevos siempre están disponibles, sin importar su due_date
        # (la DB está en UTC y su "hoy" puede ir un día adelante de Lima).
        due = (
            db.table("srs_state")
            .select("item_id, status, due_date, repetitions")
            .or_(f"status.eq.new,due_date.lte.{today.isoformat()}")
            .execute()
            .data
        )
        item_ids = choose_items(due, settings["items_per_day"])
        if session is None:
            session = (
                db.table("daily_sessions")
                .insert({"session_date": today.isoformat(), "item_ids": item_ids})
                .execute()
                .data[0]
            )
        elif item_ids:  # sesión vacía de antes: la rellenamos
            session = (
                db.table("daily_sessions")
                .update({"item_ids": item_ids})
                .eq("id", session["id"])
                .execute()
                .data[0]
            )

    if not session["item_ids"]:
        return session, []
    items = db.table("items").select("*").in_("id", session["item_ids"]).execute().data
    order = {item_id: i for i, item_id in enumerate(session["item_ids"])}
    items = sorted((it for it in items if it["id"] in order), key=lambda it: order[it["id"]])
    return session, items


def mark_morning_sent(session_id: str) -> None:
    client().table("daily_sessions").update(
        {"morning_sent_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", session_id).execute()
