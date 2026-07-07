"""API key authentication for /admin endpoints.

Keys are stored as SHA-256 hashes. Plaintext is shown once at creation
time and never recoverable — if lost, revoke and rotate.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiKey
from app.db.session import get_db_session

logger = logging.getLogger(__name__)


def hash_key(plaintext: str) -> str:
    """SHA-256 hex of the key. Deterministic by design — lookup must work."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def generate_key() -> tuple[str, str]:
    """Returns (plaintext, hash). Show plaintext once, store hash."""
    plaintext = "tk_" + secrets.token_urlsafe(32)
    return plaintext, hash_key(plaintext)


async def require_api_key(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> ApiKey:
    """FastAPI dependency. Validates Bearer token, returns the ApiKey row.

    Updates last_used_at as a side effect (for audit + key-rotation hygiene).
    """

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    plaintext = authorization[7:].strip()

    if not plaintext:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token.",
        )

    digest = hash_key(plaintext)

    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == digest)
    )

    key_row = result.scalar_one_or_none()

    if key_row is None:
        logger.warning(
            "Auth failed: unknown key hash prefix %s",
            digest[:8]
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid key.",
        )

    if key_row.revoked_at is not None:
        logger.warning(
            "Auth failed: revoked key %s",
            key_row.name
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Key revoked.",
        )

    # Update audit timestamp
    key_row.last_used_at = datetime.now(timezone.utc)

    # Persist change
    await db.commit()

    return key_row


def require_scope(scope: str):
    """Returns a dependency that also enforces a specific scope."""

    async def _check(
        key: ApiKey = Depends(require_api_key),
    ) -> ApiKey:

        if scope not in key.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
            )

        return key

    return _check
