import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AlertOut
from app.db.models import Alert
from app.db.session import AsyncSessionLocal

router = APIRouter()


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(
    target_id: uuid.UUID | None = Query(default=None),
    resolved: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    q = select(Alert).order_by(Alert.triggered_at.desc())
    if target_id is not None:
        q = q.where(Alert.target_id == target_id)
    if resolved is not None:
        q = q.where(Alert.resolved == resolved)
    alerts = (await session.execute(q)).scalars().all()
    return [AlertOut.model_validate(a) for a in alerts]