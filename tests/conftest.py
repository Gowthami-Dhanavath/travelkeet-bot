import asyncio

import pytest
import uuid



@pytest.fixture
def session_id():
    return f"test-session-{uuid.uuid4()}"
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base
from app.db.session import AsyncSessionLocal, engine


# Windows-safe event loop
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def isolate_database():
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    if not table_names:
        yield
        return

    async def truncate_tables():
        async with engine.begin() as conn:
            await conn.execute(
                text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
            )

    await truncate_tables()
    try:
        yield
    finally:
        await truncate_tables()


@pytest.fixture
async def db(isolate_database):
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()
