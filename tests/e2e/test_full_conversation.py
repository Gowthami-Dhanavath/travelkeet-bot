import pytest
from sqlalchemy import select

from app.db.models import Conversation, Message


@pytest.mark.asyncio
async def test_single_turn_persists_user_and_assistant(client, session_id, db):
    resp = await client.post(
        "/v1/chat",
        json={"session_id": session_id, "message": "hello"},
    )

    assert resp.status_code == 200
    body = resp.json()

    assert "reply" in body
    assert "conversation_id" in body
    assert "message_id" in body
    assert resp.headers.get("X-Request-ID") is not None

    conv = (await db.execute(
        select(Conversation).where(Conversation.session_id == session_id)
    )).scalar_one()

    msgs = (await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
    )).scalars().all()

    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[0].content == "hello"
    assert msgs[1].role == "assistant"
    assert msgs[1].content is not None


@pytest.mark.asyncio
async def test_three_turn_conversation_keeps_state(client, session_id, db):
    queries = [
        "Plan trip to Goa",
        "We are 4 people",
        "Budget 60000",
    ]

    conv_ids = []

    for q in queries:
        resp = await client.post(
            "/v1/chat",
            json={"session_id": session_id, "message": q},
        )
        assert resp.status_code == 200
        conv_ids.append(resp.json()["conversation_id"])

    # same conversation reused
    assert len(set(conv_ids)) == 1

    conv = (await db.execute(
        select(Conversation).where(Conversation.session_id == session_id)
    )).scalar_one()

    msgs = (await db.execute(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at)
    )).scalars().all()

    assert len(msgs) == 6  # 3 user + 3 assistant

    roles = [m.role for m in msgs]
    assert roles == ["user", "assistant", "user", "assistant", "user", "assistant"]


@pytest.mark.asyncio
async def test_session_isolation(client, db):
    s1 = "e2e-session-A"
    s2 = "e2e-session-B"

    await client.post("/v1/chat", json={"session_id": s1, "message": "hi A"})
    await client.post("/v1/chat", json={"session_id": s2, "message": "hi B"})

    convs = (await db.execute(
        select(Conversation).where(Conversation.session_id.in_([s1, s2]))
    )).scalars().all()

    assert len(convs) == 2
    assert {c.session_id for c in convs} == {s1, s2}


@pytest.mark.asyncio
async def test_error_response_shape(client):
    resp = await client.post(
        "/v1/chat",
        json={"session_id": "e2e-error", "message": "   "},
    )

    assert resp.status_code == 422
    body = resp.json()

    assert "error" in body
    assert body["error"]["code"] == "validation_error"
    assert "request_id" in body["error"]