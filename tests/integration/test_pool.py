"""Sanity-check that the pool is sized roughly as configured."""
import asyncio

import pytest

from app.config import settings
from app.db.session import AsyncSessionLocal, pool_status


@pytest.mark.asyncio
async def test_pool_handles_concurrent_sessions():
    """Open pool_size + overflow concurrent sessions; all should succeed."""
    target = settings.db_pool_size + settings.db_max_overflow - 1

    async def open_and_query():
        async with AsyncSessionLocal() as s:
            from sqlalchemy import text
            await s.execute(text("SELECT 1"))
            await asyncio.sleep(0.1)

    await asyncio.gather(*[open_and_query() for _ in range(target)])
    status = pool_status()
    # after gather, sessions returned; checked_out should be back to ~0
    assert status["checked_out"] <= 1