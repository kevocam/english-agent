"""Práctica en cadena: un ejercicio por item del día, con un reintento si fallas.

Las funciones devuelven los mensajes (HTML) a enviar; el handler los manda.
"""

import asyncio
from datetime import datetime, timezone
from html import escape

from app import db, exercises

PASS_SCORE = 3
RESULT_EMOJI = {5: "🌟", 4: "✅", 3: "👍"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_pending(session: dict) -> bool:
    return bool(session.get("current_exercise")) and session.get("status") != "done"


def _exercise_msg(session: dict, items: list[dict], prefix: str = "") -> str:
    item = items[session["current_index"]]
    head = f"🏋️ <b>Practice {session['current_index'] + 1}/{len(items)} · {escape(item['term'])}</b>"
    return f"{prefix}{head}\n{escape(session['current_exercise'])}"


def _result_msg(result: dict, answer: str) -> str:
    score = result["score"]
    text = f"{RESULT_EMOJI.get(score, '❌')} <b>{score}/5</b> · {escape(result.get('feedback', ''))}"
    corrected = (result.get("corrected") or "").strip()
    if corrected and corrected.lower() != answer.strip().lower():
        text += f"\n✏️ <i>{escape(corrected)}</i>"
    return text


DONE_MSG = (
    "🎉 <b>Done for today!</b> You practiced all your items.\n"
    "See you tomorrow at 6:00. Write to me anytime if you want to keep practicing. 💪"
)


async def _next_exercise(session: dict, items: list[dict]) -> tuple[dict, str]:
    """Prepara el ejercicio del item actual, o cierra la sesión si ya no quedan."""
    idx = session["current_index"]
    if idx >= len(items):
        session = await asyncio.to_thread(
            db.update_session, session["id"], {"status": "done", "current_exercise": None, "exercise_type": None}
        )
        return session, DONE_MSG

    item = items[idx]
    exercise_type = exercises.pick_type(item)
    text = await exercises.generate(item, exercise_type)
    session = await asyncio.to_thread(
        db.update_session,
        session["id"],
        {
            "current_exercise": text,
            "exercise_type": exercise_type,
            "exercise_sent_at": _now(),
            "retry_used": False,
            "nudge_count": 0,
            "last_nudge_at": None,
        },
    )
    return session, _exercise_msg(session, items)


async def start(session: dict, items: list[dict]) -> list[str]:
    """Arranca la práctica del día, o reenvía el ejercicio pendiente."""
    if not items:
        return []
    if session.get("status") == "done":
        return [DONE_MSG]
    if is_pending(session):
        return [_exercise_msg(session, items, prefix="↩️ ")]
    _, msg = await _next_exercise(session, items)
    return [msg]


async def handle_message(session: dict, items: list[dict], text: str, settings: dict) -> list[str]:
    """Procesa un mensaje mientras hay un ejercicio pendiente."""
    item = items[session["current_index"]]
    exercise = session["current_exercise"]
    result = await exercises.grade(item, exercise, text)

    # Pregunta → responder y volver al ejercicio (cuenta como actividad: reinicia la insistencia)
    if result.get("kind") != "answer":
        await asyncio.to_thread(
            db.update_session, session["id"], {"exercise_sent_at": _now(), "nudge_count": 0, "last_nudge_at": None}
        )
        return [f"💬 {escape(result.get('feedback', ''))}\n\n" + _exercise_msg(session, items, prefix="↩️ ")]

    score = result["score"]
    is_retry = bool(session.get("retry_used"))
    await asyncio.to_thread(
        db.save_attempt,
        {
            "session_id": session["id"],
            "item_id": item["id"],
            "exercise": exercise,
            "user_answer": text,
            "score": score,
            "feedback": result.get("feedback"),
            "attempt": 2 if is_retry else 1,
        },
    )
    if not is_retry:  # SM-2 se califica con el primer intento: es la medida honesta
        await asyncio.to_thread(db.apply_review, item["id"], score, db.today_local(settings))

    messages = [_result_msg(result, text)]

    # Primer intento fallido → un reintento con el mismo ejercicio
    if score < PASS_SCORE and not is_retry:
        await asyncio.to_thread(
            db.update_session,
            session["id"],
            {"retry_used": True, "status": "answered", "exercise_sent_at": _now(), "nudge_count": 0, "last_nudge_at": None},
        )
        messages[0] += "\n\n💡 <b>Try again:</b>\n" + escape(exercise)
        return messages

    # Aprobado (o ya se usó el reintento) → siguiente item
    session = await asyncio.to_thread(
        db.update_session,
        session["id"],
        {"current_index": session["current_index"] + 1, "retry_used": False, "status": "answered"},
    )
    _, next_msg = await _next_exercise(session, items)
    messages.append(next_msg)
    return messages
