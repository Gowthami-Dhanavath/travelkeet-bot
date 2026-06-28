import asyncio
import pytest
import pytest_asyncio

from httpx import AsyncClient

from app.db.session import AsyncSessionLocal


# =========================
# EVENT LOOP (FIXED FOR PYTEST-ASYNCIO)
# =========================
@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =========================
# DB SESSION FIXTURE (CLEAN + ISOLATED)
# =========================
@pytest_asyncio.fixture
async def db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # rollback ensures NO cross-test pollution
            await session.rollback()
            await session.close()


# =========================
# HTTP CLIENT FIXTURE (if your tests use FastAPI app)
# =========================
@pytest_asyncio.fixture
async def client():
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
         