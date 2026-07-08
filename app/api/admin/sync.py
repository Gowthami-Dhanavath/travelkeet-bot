"""Admin endpoint for manual data sync."""
import logging

from fastapi import APIRouter, HTTPException

from app.deps import AdminKey
from app.integrations.travelkeet_sync import sync_campervans

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/data/sync")
async def trigger_sync(key: AdminKey):
    """Manually trigger the campervan inventory sync."""
    try:
        result = await sync_campervans()
    except Exception as e:
        logger.exception("Manual sync failed")
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")
    return {"status": "ok", **result}