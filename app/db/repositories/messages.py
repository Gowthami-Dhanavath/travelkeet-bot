"""Repository for the messages table."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message

logger = logging.getLogger(__name__)


class MessageRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append(
        self,
        conversation_id: UUID,
        role: str,
        content: str | None = None,
        tool_calls: dict | list | None = None,
        tool_results: dict | None = None,
        model: str | None = None,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        latency_ms: int | None = None,
        prompt_version: str | None = None,
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
        self.session.add(msg)
        await self.session.flush()
        logger.info(
            "DB message written",
            extra={
                "conversation_id": str(conversation_id),
                "message_id": str(msg.id),
                "role": role,
            },
        )
        return msg

    async def get_window(
        self, conversation_id: UUID, max_turns: int = 15
    ) -> list[Message]:
        """Return the last (max_turns * 2) messages in chronological order.

        Used by the agent to build the messages array sent to Claude.
        """
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(max_turns * 2)
        )
        msgs = list(result.scalars().all())
        msgs.reverse()  # chronological for Claude
        return msgs

    async def count(self, conversation_id: UUID) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        return result.scalar_one()
