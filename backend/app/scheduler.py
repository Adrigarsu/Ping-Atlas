import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.api.probes import _execute_probe
from app.db.models import Target
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


async def _probe_all_enabled() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Target).where(Target.enabled.is_(True)))
        targets = result.scalars().all()

    for target in targets:
        try:
            await _execute_probe(target.host)
        except Exception as exc:
            logger.warning("Scheduled probe for %s failed: %s", target.host, exc)


def start() -> None:
    interval = int(os.environ.get("PROBE_INTERVAL_SECONDS", "300"))
    _scheduler.add_job(_probe_all_enabled, "interval", seconds=interval, id="probe_all")
    _scheduler.start()
    logger.info("Scheduler started — probing every %d s", interval)


def stop() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")