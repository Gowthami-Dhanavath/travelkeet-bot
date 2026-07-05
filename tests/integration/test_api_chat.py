"""Integration tests for the /v1/chat endpoint."""
import pytest
import uuid
from uuid import uuid4
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

from app.agent.schemas import AgentResponse
from app.db.repositories import ConversationRepo, MessageRepo
from app.deps import get_conversation_repo, get_message_repo, get_orchestrator
from app.main import app


@pytest.fixture(autouse=True)
def stub_orchestrator():
    class StubAgentResponse(AgentResponse):
        def get(self, key, default=None):
            if key == "reply":
                return self.text
            return getattr(self, key, default)

    class FakeOrch:
        def __init__(self, conv_repo, msg_repo):
            self.conv_repo = conv_repo
            self.msg_repo = msg_repo

        async def handle_message(self, session_id, user_message, **kwargs):
            conversation = await self.conv_repo.get_or_create(session_id=session_id)
            await self.msg_repo.append(
                conversation_id=conversation.id,
                role="user",
                content=user_message,
            )
            assistant_message = await self.msg_repo.append(
                conversation_id=conversation.id,
                role="assistant",
                content="stubbed",
                tool_calls=[],
            )
            return StubAgentResponse(
                text="stubbed",
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                tool_calls=[],
                slots={},
            )

    async def fake_orchestrator(
        conv_repo: ConversationRepo = Depends(get_conversation_repo),
        msg_repo: MessageRepo = Depends(get_message_repo),
    ):
        return FakeOrch(conv_repo=conv_repo, msg_repo=msg_repo)

    app.dependency_overrides[get_orchestrator] = fake_orchestrator
    yield
    app.dependency_overrides.clear()


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
    assert resp.json()["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_chat_honors_incoming_request_id(monkeypatch):
    """Verifies X-Request-ID middleware without hitting Groq.
    Mocks the orchestrator so the test is fast, deterministic, and free."""
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

    session_id = f"chat-persist-{uuid.uuid4()}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/v1/chat",
            json={
                "session_id": session_id,
                "message": "remember me",
            },
        )

    conv = (
        await db.execute(
            select(Conversation).where(
                Conversation.session_id == session_id
            )
        )
    ).scalar_one_or_none()

    assert conv is not None

    msgs = (
        await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at)
        )
    ).scalars().all()

    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[0].content == "remember me"
    assert msgs[1].role == "assistant"
