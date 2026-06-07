import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class ProbeRequest(BaseModel):
    target: str

    @field_validator("target")
    @classmethod
    def target_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("target must not be empty")
        return v


class HopOut(BaseModel):
    ttl: int
    ip: str | None
    rtt_ms: float | None
    latitude: float | None
    longitude: float | None
    city: str | None
    country: str | None
    asn: str | None

    model_config = {"from_attributes": True}


class ProbeOut(BaseModel):
    id: uuid.UUID
    target_id: uuid.UUID
    started_at: datetime
    finished_at: datetime | None
    rtt_ms: float | None
    packet_loss: float | None
    hops: list[HopOut] = []

    model_config = {"from_attributes": True}


class ProbeCreated(BaseModel):
    probe_id: uuid.UUID


class PaginatedProbes(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ProbeOut]


class RouteOut(BaseModel):
    target_id: uuid.UUID
    hops: list[tuple[float, float]]