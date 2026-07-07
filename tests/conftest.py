import os

os.environ["groq_api_key"] = "test-key"
import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation
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
            await session.execute(
                delete(Conversation).where(
                    Conversation.session_id.like("test-api-sess-%")
                )
            )
            await session.commit()
            yield session
        finally:
            await session.rollback()  # prevents cross-test pollution
            await session.close()
class FakeGroqClient:

    async def generate_with_tools(
        self,
        system_instruction,
        history,
        tool_declarations,
    ):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Hello! How can I help you plan your trip?",
                        tool_calls=[],
                    ),
                ),
            ],
            latency_ms=0,
        )


@pytest.fixture(autouse=True)
def fake_groq_client(monkeypatch):
    monkeypatch.setattr("app.deps.get_groq_model", lambda: FakeGroqClient())
