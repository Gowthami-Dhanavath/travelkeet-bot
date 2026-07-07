"""Minimal admin endpoint to prove the auth dependency is wired.

Real admin endpoints (leads, conversations, metrics) come Days 11, 25.
"""
from datetime import datetime, timezone

from fastapi import APIRouter

from app.deps import AdminKey

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/whoami")
async def whoami(key: AdminKey):
    return {
        "key_name": key.name,
        "scopes": key.scopes,
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
    
