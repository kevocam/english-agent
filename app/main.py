from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import config
from app.bot.handlers import build_application


@asynccontextmanager
async def lifespan(_: FastAPI):
    tg = build_application()
    await tg.initialize()
    await tg.start()
    if config.MODE == "polling":
        await tg.updater.start_polling(drop_pending_updates=True)
    # MODE=webhook se agrega al hacer el deploy en Railway
    try:
        yield
    finally:
        if tg.updater.running:
            await tg.updater.stop()
        await tg.stop()
        await tg.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "mode": config.MODE}
