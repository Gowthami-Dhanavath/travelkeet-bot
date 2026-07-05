"""Integration tests for /v1/chat/stream."""
import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.models import Conversation, Message
from app.main import app


@pytest.mark.asyncio
async def test_stream_yields_multiple_token_events():
    """Streaming must fragment into multiple token events, not one blob."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60) as client:
        async with client.stream(
            "POST", "/v1/chat/stream",
            json={
                "session_id": "stream-test-multi-001",
                "message": "hello",
            },
        ) as resp:
            assert resp.status_code == 200
            text = ""
            async for chunk in resp.aiter_text():
                text += chunk

    # At least 2 token events + a done event
    token_events = text.count("event: token")
    assert token_events >= 2, f"expected >=2 token events, got {token_events}"
    assert "event: done" in text


@pytest.mark.asyncio
async def test_stream_persists_user_and_assistant_exactly_once(db):
    """Guards the Day 11 double-persist bug: user=1, assistant=1 per turn."""
    sid = f"stream-test-persist-{uuid.uuid4()}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60) as client:
        async with client.stream(
            "POST", "/v1/chat/stream",
            json={"session_id": sid, "message": "hi"},
        ) as resp:
            async for _ in resp.aiter_text():
                pass

    conv = (await db.execute(
        select(Conversation).where(Conversation.session_id == sid)
    )).scalar_one()
    msgs = (await db.execute(
        select(Message).where(Message.conversation_id == conv.id)
    )).scalars().all()
    by_role = {}
    for m in msgs:
        by_role[m.role] = by_role.get(m.role, 0) + 1
    assert by_role.get("user") == 1, f"expected exactly 1 user msg, got {by_role}"
    assert by_role.get("assistant") == 1, f"expected exactly 1 assistant msg, got {by_role}"


@pytest.mark.asyncio
async def test_stream_rejects_empty_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/chat/stream",
            json={"session_id": "stream-test-empty-001", "message": "   "},
        )
    assert resp.status_code == 422