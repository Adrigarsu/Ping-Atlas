import socket
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.anomaly import check_and_alert
from app.api.schemas import PaginatedProbes, ProbeCreated, ProbeOut, ProbeRequest, RouteOut, TargetOut
from app.api.ws import HopMessage, manager
from app.db.models import Hop, Probe, Target
from app.db.session import AsyncSessionLocal
from app.limiter import limiter
from app.probe import geoip
from app.probe.traceroute import traceroute_stream

router = APIRouter()


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


async def _get_or_create_target(session: AsyncSession, host: str) -> Target:
    result = await session.execute(select(Target).where(Target.host == host))
    target = result.scalar_one_or_none()
    if target is None:
        target = Target(id=uuid.uuid4(), host=host, created_at=datetime.now(UTC))
        session.add(target)
        await session.flush()
    return target


async def _execute_probe(host: str) -> uuid.UUID:
    """Run a full traceroute probe for host, persist results, and broadcast WS hops.

    Raises ValueError if the host cannot be resolved.
    """
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        raise ValueError(f"Cannot resolve hostname: '{host}'")

    async with AsyncSessionLocal() as session:
        target = await _get_or_create_target(session, host)

        started_at = datetime.now(UTC)
        probe = Probe(id=uuid.uuid4(), target_id=target.id, started_at=started_at)
        session.add(probe)
        await session.flush()

        rtts: list[float] = []
        total = 0

        async for hop in traceroute_stream(ip):
            total += 1
            geo = geoip.resolve(hop.ip) if hop.ip else geoip.GeoResult(None, None, None, None)
            if hop.rtt_ms is not None:
                rtts.append(hop.rtt_ms)

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

            await manager.broadcast(
                HopMessage(
                    probe_id=probe.id,
                    ttl=hop.ttl,
                    ip=hop.ip,
                    rtt_ms=hop.rtt_ms,
                    lat=geo.latitude,
                    lon=geo.longitude,
                    country=geo.country,
                    city=geo.city,
                )
            )

        probe.finished_at = datetime.now(UTC)
        probe.rtt_ms = sum(rtts) / len(rtts) if rtts else None
        probe.packet_loss = ((total - len(rtts)) / total * 100) if total else None

        if probe.rtt_ms is not None:
            await check_and_alert(session, target.id, probe.id, probe.rtt_ms)

        await session.commit()
        return probe.id


@router.post("/probe", response_model=ProbeCreated, status_code=202)
@limiter.limit("10/minute")
async def run_probe(request: Request, response: Response, body: ProbeRequest) -> ProbeCreated:
    try:
        probe_id = await _execute_probe(body.target)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ProbeCreated(probe_id=probe_id)


@router.get("/routes/{target_id}", response_model=RouteOut)
async def get_route(
    target_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> RouteOut:
    result = await session.execute(select(Target).where(Target.id == target_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail=f"Target '{target_id}' not found")

    latest_probe = (
        await session.execute(
            select(Probe)
            .where(Probe.target_id == target_id)
            .where(Probe.finished_at.is_not(None))
            .order_by(Probe.started_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if latest_probe is None:
        return RouteOut(target_id=target_id, hops=[])

    hops = (
        await session.execute(
            select(Hop)
            .where(Hop.probe_id == latest_probe.id)
            .where(Hop.latitude.is_not(None))
            .where(Hop.longitude.is_not(None))
            .order_by(Hop.ttl)
        )
    ).scalars().all()

    return RouteOut(
        target_id=target_id,
        hops=[(h.latitude, h.longitude) for h in hops],  # type: ignore[misc]
    )


@router.get("/targets", response_model=list[TargetOut])
async def list_targets(session: AsyncSession = Depends(get_db)) -> list[TargetOut]:
    targets = (await session.execute(select(Target).order_by(Target.created_at))).scalars().all()
    return [TargetOut.model_validate(t) for t in targets]


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