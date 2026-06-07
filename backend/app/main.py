from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.probe import geoip


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    geoip.init()
    yield


app = FastAPI(title="PingAtlas", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}