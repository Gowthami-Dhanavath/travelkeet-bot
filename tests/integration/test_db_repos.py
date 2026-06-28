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


@pytest.mark.asyncio
async def test_get_window_returns_empty_for_new_conversation(db):
    conv_repo = ConversationRepo(db)
    msg_repo = MessageRepo(db)

    conv = await conv_repo.get_or_create(session_id="window-empty-1")

    window = await msg_repo.get_window(conv.id, max_turns=15)

    assert window == []


@pytest.mark.asyncio
async def test_get_window_includes_tool_role_messages(db):
    conv_repo = ConversationRepo(db)
    msg_repo = MessageRepo(db)

    conv = await conv_repo.get_or_create(session_id="window-tool-1")

    await msg_repo.append(
        conv.id,
        role="user",
        content="find me a van"
    )

    await msg_repo.append(
        conv.id,
        role="assistant",
        content=None,
        tool_calls={
            "name": "search_campervans",
            "args": {"city": "Mumbai"}
        }
    )

    await msg_repo.append(
        conv.id,
        role="tool",
        content=None,
        tool_results={
            "results": [{"id": "TK-AURA-01"}]
        }
    )

    await msg_repo.append(
        conv.id,
        role="assistant",
        content="I found one van."
    )

    window = await msg_repo.get_window(conv.id, max_turns=15)

    roles = [m.role for m in window]

    assert roles == [
        "user",
        "assistant",
        "tool",
        "assistant"
    ]


@pytest.mark.asyncio
async def test_get_window_chronological_order(db):
    conv_repo = ConversationRepo(db)
    msg_repo = MessageRepo(db)

    conv = await conv_repo.get_or_create(session_id="window-order-1")

    for i in range(6):
        await msg_repo.append(
            conv.id,
            role="user",
            content=f"msg-{i}"
        )

    window = await msg_repo.get_window(
        conv.id,
        max_turns=15
    )

    assert [m.content for m in window] == [
        f"msg-{i}" for i in range(6)
    ]


@pytest.mark.asyncio
async def test_get_window_returns_empty_for_new_conversation_duplicate(db):
    conv_repo = ConversationRepo(db)
    msg_repo = MessageRepo(db)

    conv = await conv_repo.get_or_create(
        session_id="window-empty-1"
    )

    window = await msg_repo.get_window(
        conv.id,
        max_turns=15
    )

    assert window == []


@pytest.mark.asyncio
async def test_get_window_includes_tool_role_messages_duplicate(db):
    conv_repo = ConversationRepo(db)
    msg_repo = MessageRepo(db)

    conv = await conv_repo.get_or_create(
        session_id="window-tool-1"
    )

    await msg_repo.append(
        conv.id,
        role="user",
        content="find me a van"
    )

    await msg_repo.append(
        conv.id,
        role="assistant",
        content=None,
        tool_calls={
            "name": "search_campervans",
            "args": {
                "city": "Mumbai"
            }
        }
    )

    await msg_repo.append(
        conv.id,
        role="tool",
        content=None,
        tool_results={
            "results": [
                {
                    "id": "TK-AURA-01"
                }
            ]
        }
    )

    await msg_repo.append(
        conv.id,
        role="assistant",
        content="I found one van."
    )

    window = await msg_repo.get_window(
        conv.id,
        max_turns=15
    )

    roles = [m.role for m in window]

    assert roles == [
        "user",
        "assistant",
        "tool",
        "assistant"
    ]


@pytest.mark.asyncio
async def test_get_window_chronological_order_duplicate(db):
    conv_repo = ConversationRepo(db)
    msg_repo = MessageRepo(db)

    conv = await conv_repo.get_or_create(
        session_id="window-order-1"
    )

    for i in range(6):
        await msg_repo.append(
            conv.id,
            role="user",
            content=f"msg-{i}"
        )

    window = await msg_repo.get_window(
        conv.id,
        max_turns=15
    )

    assert [
        m.content for m in window
    ] == [
        f"msg-{i}" for i in range(6)
    ]