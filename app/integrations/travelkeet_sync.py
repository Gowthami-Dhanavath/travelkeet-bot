"""Sync campervan inventory from the TravelKeet upstream feed.

The site team's live feed isn't available yet; today the sync reads
from the seed JSON. When the feed URL is ready, set SYNC_FEED_URL and
the sync switches to HTTP automatically — no code changes.

Per the compressed launch plan risk note: 'If the feed isn't available,
ship against a seeded snapshot and make live sync the first month-2 item.'
"""
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.db.repositories import CampervanRepo
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

SEED_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "campervans.seed.json"
)


async def fetch_inventory() -> list[dict[str, Any]]:
    """Fetch the upstream inventory."""
    feed_url = getattr(settings, "sync_feed_url", "")
    if feed_url:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
            data = response.json()
        logger.info("Fetched inventory from feed", extra={"url": feed_url, "count": len(data)})
    else:
        logger.info("SYNC_FEED_URL not set; using seed snapshot")
        data = json.loads(SEED_PATH.read_text())

    if not isinstance(data, list):
        raise ValueError(f"Feed returned {type(data).__name__}, expected list")
    return data


async def sync_campervans() -> dict[str, Any]:
    """Fetch and upsert. Returns {'upserted': N, 'deactivated': N}."""
    vans = await fetch_inventory()

    async with AsyncSessionLocal() as session:
        try:
            repo = CampervanRepo(session)
            upserted = await repo.upsert_many(vans)
            current_ids = {v["id"] for v in vans}
            deactivated = await repo.deactivate_missing(current_ids)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    logger.info(
        "Campervan sync complete",
        extra={"upserted": upserted, "deactivated": deactivated},
    )
    return {"upserted": upserted, "deactivated": deactivated}