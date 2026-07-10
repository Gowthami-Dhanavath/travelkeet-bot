"""Integration tests for the /v1/chat endpoint."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_chat_creates_conversation_and_persists_messages():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/chat",
            json={"session_id": "test-api-sess-1", "message": "Hello there"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert "reply" in body
    assert "conversation_id" in body
    assert "message_id" in body
    assert "X-Request-ID" in resp.headers


@pytest.mark.asyncio
async def test_chat_reuses_existing_conversation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(
            "/v1/chat",
            json={"session_id": "test-api-sess-2", "message": "first"},
        )
        r2 = await client.post(
            "/v1/chat",
            json={"session_id": "test-api-sess-2", "message": "second"},
        )
    assert r1.json()["conversation_id"] == r2.json()["conversation_id"]
    assert r1.json()["message_id"] != r2.json()["message_id"]


@pytest.mark.asyncio
async def test_chat_rejects_short_session_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/chat",
            json={"session_id": "abc", "message": "hi"},
        )
    assert resp.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_chat_rejects_whitespace_only_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/chat",
            json={"session_id": "test-api-sess-3", "message": "   "},
        )
    assert resp.status_code == 422
    assert "detail" in resp.json()


@pytest.mark.asyncio
async def test_chat_honors_incoming_request_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/chat",
            headers={"X-Request-ID": "my-custom-trace-id"},
            json={"session_id": "test-api-sess-4", "message": "trace me"},
        )
    assert resp.headers["X-Request-ID"] == "my-custom-trace-id"


@pytest.mark.asyncio
async def test_chat_persists_user_message_to_db(db):
    """End-to-end: hit API, then read DB to confirm rows exist."""
    from sqlalchemy import select
    from app.db.models import Conversation, Message

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/v1/chat",
            json={"session_id": "test-api-sess-5", "message": "remember me"},
        )

    # Fresh session — the test client uses its own session, so we read with ours
    conv = (await db.execute(
        select(Conversation).where(Conversation.session_id == "test-api-sess-5")
    )).scalar_one_or_none()
    assert conv is not None

    msgs = (await db.execute(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
    )).scalars().all()
    assert len(msgs) == 2  # user + stub assistant
    assert msgs[0].role == "user"
    assert msgs[0].content == "remember me"
    assert msgs[1].role == "assistant"
