import asyncio
import json
import logging
import os
import urllib.request
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert, Probe

logger = logging.getLogger(__name__)

_ROLLING_WINDOW = 10


async def check_and_alert(
    session: AsyncSession,
    target_id: uuid.UUID,
    probe_id: uuid.UUID,
    current_rtt: float,
) -> Alert | None:
    threshold = float(os.environ.get("LATENCY_ALERT_DELTA_MS", "50"))

    recent_rtts = (
        await session.execute(
            select(Probe.rtt_ms)
            .where(Probe.target_id == target_id)
            .where(Probe.id != probe_id)
            .where(Probe.rtt_ms.is_not(None))
            .where(Probe.finished_at.is_not(None))
            .order_by(Probe.started_at.desc())
            .limit(_ROLLING_WINDOW)
        )
    ).scalars().all()

    if not recent_rtts:
        return None

    rolling_avg = sum(recent_rtts) / len(recent_rtts)
    delta = current_rtt - rolling_avg

    if delta <= threshold:
        return None

    alert = Alert(
        id=uuid.uuid4(),
        target_id=target_id,
        probe_id=probe_id,
        triggered_at=datetime.now(UTC),
        rtt_ms=current_rtt,
        rolling_avg_ms=rolling_avg,
        delta_ms=delta,
    )
    session.add(alert)

    logger.warning(
        "Latency spike detected for target %s: %.1f ms (rolling avg %.1f ms, delta %.1f ms)",
        target_id,
        current_rtt,
        rolling_avg,
        delta,
    )

    await _send_webhook(alert)
    return alert


async def _send_webhook(alert: Alert) -> None:
    url = os.environ.get("ALERT_WEBHOOK_URL", "")
    if not url:
        return

    payload = json.dumps(
        {
            "target_id": str(alert.target_id),
            "probe_id": str(alert.probe_id),
            "triggered_at": alert.triggered_at.isoformat(),
            "rtt_ms": alert.rtt_ms,
            "rolling_avg_ms": alert.rolling_avg_ms,
            "delta_ms": alert.delta_ms,
        }
    ).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, urllib.request.urlopen, req)
    except Exception as exc:
        logger.warning("Webhook delivery to %s failed: %s", url, exc)