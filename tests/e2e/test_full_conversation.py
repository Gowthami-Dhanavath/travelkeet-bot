import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.db.models import Conversation, ToolCall


@pytest.mark.asyncio
async def test_tool_call_is_recorded(db, session_id):

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        messages = [
            "Mumbai to Goa trip",
            "4 adults vegetarian budget 60000",
        ]

        for message in messages:
            await client.post(
                "/v1/chat",
                json={
                    "session_id": session_id,
                    "message": message,
                },
            )


    conv = (
        await db.execute(
            select(Conversation)
            .where(
                Conversation.session_id == session_id
            )
        )
    ).scalar_one()


    tools = (
        await db.execute(
            select(ToolCall)
            .where(
                ToolCall.conversation_id == conv.id
            )
        )
    ).scalars().all()


    assert any(
        t.tool_name == "search_campervans"
        for t in tools
    )

    assert any(
        t.success
        for t in tools
    )