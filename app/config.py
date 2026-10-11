import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

REQUIRED = ("TELEGRAM_BOT_TOKEN", "SUPABASE_URL", "SUPABASE_KEY")
_missing = [name for name in REQUIRED if not os.getenv(name)]
if _missing:
    raise RuntimeError(
        f"Faltan variables de entorno: {', '.join(_missing)}. "
        "En local: revisa .env. En Railway: Variables del servicio + redeploy."
    )

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/").removesuffix("/rest/v1")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODE = os.getenv("MODE", "polling")  # polling (local/VPS) | webhook (Railway)
