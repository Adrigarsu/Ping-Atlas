import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import scheduler
from app.api.probes import router as probes_router
from app.api.ws import router as ws_router
from app.probe import geoip


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        geoip.init()
    except geoip.ConfigurationError as exc:
        logging.warning("GeoIP unavailable — geolocation will be disabled: %s", exc)

    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="PingAtlas", lifespan=lifespan)

app.include_router(probes_router)
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}