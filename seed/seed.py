"""Carga una lección (JSON) en Supabase.

Uso:
    python seed/seed.py                 # carga seed/lesson-1.json
    python seed/seed.py seed/lesson-2.json

Es idempotente: si lo corres dos veces actualiza en vez de duplicar.
El estado SM-2 de cada item nuevo lo crea un trigger en la DB.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = Path(__file__).resolve().parent / "lesson-1.json"


def main() -> None:
    load_dotenv(ROOT / ".env")
    url = os.environ["SUPABASE_URL"].rstrip("/").removesuffix("/rest/v1")
    key = os.environ["SUPABASE_KEY"]  # secret / service_role key (RLS está activo)

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FILE
    data = json.loads(path.read_text(encoding="utf-8"))
    lesson = data["lesson"]

    db = create_client(url, key)

    contexts = data.get("contexts", [])
    if contexts:
        db.table("contexts").upsert(contexts, on_conflict="name").execute()

    items = [{**item, "lesson": lesson} for item in data["items"]]
    db.table("items").upsert(items, on_conflict="term,type").execute()

    print(f"✅ {lesson}: {len(items)} items y {len(contexts)} contextos cargados")


if __name__ == "__main__":
    main()
