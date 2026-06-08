import pytest
from app.db.repositories import ConversationRepo, MessageRepo


@pytest.mark.asyncio
async def test_get_or_create_creates_when_missing(db):
    repo = ConversationRepo(db)
    conv = await repo.get_or_create(session_id="test-sess-1")
    assert conv.session_id == "test-sess-1"


@pytest.mark.asyncio
async def test_message_append_and_window(db):
    conv_repo = ConversationRepo(db)
    msg_repo = MessageRepo(db)

    conv = await conv_repo.get_or_create(session_id="test-sess-2")

    await msg_repo.append(conv.id, role="user", content="hello")
    await msg_repo.append(conv.id, role="assistant", content="hi")

    window = await msg_repo.get_window(conv.id, max_turns=15)

    assert len(window) == 2