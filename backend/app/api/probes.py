import socket
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas import PaginatedProbes, ProbeCreated, ProbeOut, ProbeRequest
from app.db.models import Hop, Probe, Target
from app.db.session import AsyncSessionLocal
from app.probe import geoip
from app.probe.traceroute import traceroute

router = APIRouter()


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


def _resolve_host(target: str) -> str:
    try:
        return socket.gethostbyname(target)
    except socket.gaierror:
        raise HTTPException(status_code=422, detail=f"Cannot resolve hostname: '{target}'")


async def _get_or_create_target(session: AsyncSession, host: str) -> Target:
    result = await session.execute(select(Target).where(Target.host == host))
    target = result.scalar_one_or_none()
    if target is None:
        target = Target(id=uuid.uuid4(), host=host, created_at=datetime.now(timezone.utc))
        session.add(target)
        await session.flush()
    return target


@router.post("/probe", response_model=ProbeCreated, status_code=202)
async def run_probe(
    body: ProbeRequest,
    session: AsyncSession = Depends(get_db),
) -> ProbeCreated:
    ip = _resolve_host(body.target)
    target = await _get_or_create_target(session, body.target)

    started_at = datetime.now(timezone.utc)
    probe = Probe(
        id=uuid.uuid4(),
        target_id=target.id,
        started_at=started_at,
    )
    session.add(probe)
    await session.flush()

    hops = traceroute(ip)
    rtts = [h.rtt_ms for h in hops if h.rtt_ms is not None]
    total = len(hops)
    timeouts = sum(1 for h in hops if h.rtt_ms is None)

    for hop in hops:
        geo = geoip.resolve(hop.ip) if hop.ip else geoip.GeoResult(None, None, None, None)
        session.add(
            Hop(
                id=uuid.uuid4(),
                probe_id=probe.id,
                started_at=started_at,
                ttl=hop.ttl,
                ip=hop.ip,
                rtt_ms=hop.rtt_ms,
                latitude=geo.latitude,
                longitude=geo.longitude,
                city=geo.city,
                country=geo.country,
                asn=None,
            )
        )

    probe.finished_at = datetime.now(timezone.utc)
    probe.rtt_ms = sum(rtts) / len(rtts) if rtts else None
    probe.packet_loss = (timeouts / total * 100) if total else None

    await session.commit()
    return ProbeCreated(probe_id=probe.id)


@router.get("/results", response_model=PaginatedProbes)
async def list_results(
    target: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> PaginatedProbes:
    q = select(Probe).options(selectinload(Probe.hops))

    if target:
        result = await session.execute(select(Target).where(Target.host == target))
        t = result.scalar_one_or_none()
        if t is None:
            return PaginatedProbes(total=0, limit=limit, offset=offset, items=[])
        q = q.where(Probe.target_id == t.id)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await session.execute(count_q)).scalar_one()

    probes = (await session.execute(q.order_by(Probe.started_at.desc()).limit(limit).offset(offset))).scalars().all()

    return PaginatedProbes(
        total=total,
        limit=limit,
        offset=offset,
        items=[ProbeOut.model_validate(p) for p in probes],
    )
