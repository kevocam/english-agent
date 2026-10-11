"""Repaso espaciado: selección diaria + algoritmo SM-2."""

import random
from datetime import date, timedelta

MASTERED_INTERVAL_DAYS = 21  # si el próximo repaso es en 3+ semanas, se considera dominado


def sm2(state: dict, quality: int, today: date) -> dict:
    """Aplica SM-2 (el de Anki clásico) y devuelve los campos nuevos de srs_state.

    quality: 0–5. Menos de 3 = fallo → vuelve mañana y se reinicia la racha.
    """
    q = max(0, min(5, quality))
    ef = float(state["ease_factor"])
    reps = state["repetitions"]
    interval = state["interval_days"]

    if q < 3:
        reps, interval = 0, 1
    else:
        reps += 1
        if reps == 1:
            interval = 1
        elif reps == 2:
            interval = 6
        else:
            interval = round(interval * ef)
    ef = max(1.3, ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))

    return {
        "ease_factor": round(ef, 2),
        "repetitions": reps,
        "interval_days": interval,
        "due_date": (today + timedelta(days=interval)).isoformat(),
        "status": "mastered" if interval >= MASTERED_INTERVAL_DAYS else "learning",
    }


def choose_items(due_rows: list[dict], n: int, rng: random.Random | None = None) -> list[str]:
    """Elige hasta `n` item_ids para hoy.

    - Repasos vencidos primero (los más atrasados antes), pero dejando al menos
      1 cupo para algo nuevo si queda contenido sin ver.
    - Los nuevos se eligen al azar para mezclar vocab, phrasal, idioms y gramática.
    """
    rng = rng or random.Random()
    reviews = sorted((r for r in due_rows if r["status"] != "new"), key=lambda r: r["due_date"])
    new = [r for r in due_rows if r["status"] == "new"]
    rng.shuffle(new)

    review_slots = n - 1 if new else n
    picked = reviews[:review_slots]
    picked += new[: n - len(picked)]
    if len(picked) < n:  # no alcanzaron los nuevos: completar con más repasos
        picked += reviews[review_slots : review_slots + n - len(picked)]
    return [r["item_id"] for r in picked]
