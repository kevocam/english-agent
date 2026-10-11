"""Repaso espaciado. Por ahora solo la selección diaria; la calificación SM-2 llega en la historia 6."""

import random


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
