"""Day 16 safety hardening tests."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.db.models import Conversation, Message
from app.main import app


@pytest.mark.asyncio
async def test_rejects_invalid_session_id_chars():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/chat", json={
            "session_id": "bad;drop table",
            "message": "hi",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rejects_short_session_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/chat", json={
            "session_id": "short",
            "message": "hi",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rejects_control_chars_in_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/chat", json={
            "session_id": "safetytest001",
            "message": "hello\x00world",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_rejects_whitespace_only_message():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/chat", json={
            "session_id": "safetytest002",
            "message": "   ",
        })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_turn_cap_enforced(db):
    """26th user turn on same conversation returns 429."""
    from app.api.v1.chat import MAX_USER_TURNS_PER_CONVERSATION
    from app.db.repositories.conversations import ConversationRepo
    from app.db.repositories.messages import MessageRepo

    sid = "turncaptest0001"
    conv_repo = ConversationRepo(db)
    msg_repo = MessageRepo(db)
    conv = await conv_repo.get_or_create(session_id=sid)

    # Preseed MAX user messages
    for i in range(MAX_USER_TURNS_PER_CONVERSATION):
        await msg_repo.append(
            conversation_id=conv.id,
            role="user",
            content=f"preseed turn {i}",
        )
    await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/chat", json={
            "session_id": sid,
            "message": "one turn too many",
        })
    assert r.status_code == 429