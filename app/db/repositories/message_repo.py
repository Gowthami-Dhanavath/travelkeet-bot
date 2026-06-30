from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Message


class MessageRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def append(
    self,
    conversation_id,
    role,
    content=None,
    tool_calls=None,
    tool_results=None,
    model=None,
    tokens_in=None,
    tokens_out=None,
    latency_ms=None,
    prompt_version=None,
) -> Message:

    if role not in {"user", "assistant", "tool"}:
        raise ValueError(f"Invalid role: {role}")

    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        tool_calls=tool_calls,
        tool_results=tool_results,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        prompt_version=prompt_version,
    )

    # ❌ CRITICAL: DO NOT check existing, DO NOT query, DO NOT dedupe
    # ❌ ANY SELECT HERE = causes test duplication side-effects

    self.session.add(msg)
    await self.session.flush()

    return msg