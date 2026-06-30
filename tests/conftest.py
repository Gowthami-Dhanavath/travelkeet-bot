import asyncio
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base
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
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(
                text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
            )
            await session.commit()
            yield session
        finally:
            await session.rollback()  # prevents cross-test pollution
            await session.execute(
                text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
            )
            await session.commit()
            await session.close()
import uuid

@pytest.fixture
def session_id():
    return f"test-{uuid.uuid4()}"