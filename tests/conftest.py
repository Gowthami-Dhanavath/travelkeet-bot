import pytest
import asyncio
from app.db.session import AsyncSessionLocal


# Windows-safe event loop
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Correct DB fixture (THIS FIXES YOUR ERROR)
@pytest.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session