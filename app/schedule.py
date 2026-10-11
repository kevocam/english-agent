"""Reglas de horario: silencio nocturno, clases, pausa y hora de la mañana.

Funciones puras (sin DB ni Telegram) para poder testearlas fácil.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _t(value: str) -> time:
    return time.fromisoformat(value)


def local_now(settings: dict, now: datetime | None = None) -> datetime:
    tz = ZoneInfo(settings["timezone"])
    return (now or datetime.now(tz)).astimezone(tz)


def is_sleeping(settings: dict, now: datetime) -> bool:
    start, end, t = _t(settings["sleep_start"]), _t(settings["sleep_end"]), now.time()
    if start <= end:
        return start <= t < end
    return t >= start or t < end  # cruza medianoche (23:30 → 05:50)


def in_class(settings: dict, now: datetime) -> bool:
    day = DAYS[now.weekday()]
    t = now.time()
    return any(
        block["day"] == day and _t(block["start"]) <= t < _t(block["end"])
        for block in settings.get("class_schedule") or []
    )


def is_paused(settings: dict, now: datetime) -> bool:
    until = settings.get("paused_until")
    return bool(until) and now < datetime.fromisoformat(until)


def is_quiet(settings: dict, now: datetime) -> bool:
    """True si el bot NO debe escribir ahora."""
    return is_sleeping(settings, now) or in_class(settings, now) or is_paused(settings, now)


def nudge_due(settings: dict, now: datetime, session: dict) -> bool:
    """¿Toca insistir con el ejercicio pendiente? Intervalos 10 → 20 → 40 (luego cada 40)."""
    if not session.get("current_exercise") or session.get("status") == "done" or is_quiet(settings, now):
        return False
    ref = session.get("last_nudge_at") or session.get("exercise_sent_at")
    if not ref:
        return False
    intervals = settings.get("nudge_intervals_min") or [10, 20, 40]
    wait_min = intervals[min(session.get("nudge_count") or 0, len(intervals) - 1)]
    elapsed_min = (now - datetime.fromisoformat(ref)).total_seconds() / 60
    return elapsed_min >= wait_min


def morning_due(settings: dict, now: datetime, already_sent: bool) -> bool:
    """¿Toca mandar el mensaje de la mañana?

    Si el server estuvo caído a las 6am, lo manda apenas vuelva (mientras no sea de noche).
    """
    return (
        not already_sent
        and settings.get("telegram_chat_id") is not None
        and now.time() >= _t(settings["morning_time"])
        and not is_quiet(settings, now)
    )
