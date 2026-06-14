import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


# Windows-safe event loop
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ✅ FIXED DB SESSION (CRITICAL)
@pytest.fixture
async def db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()  # prevents cross-test pollution
            await session.close()