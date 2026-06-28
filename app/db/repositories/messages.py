"""Repository for the messages table."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message


class MessageRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append(
        self,
        conversation_id: UUID,
        role: str,
        content: str | None = None,
        tool_calls: dict | None = None,
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
            created_at=datetime.now(timezone.utc),
        )

        self.session.add(msg)
        await self.session.flush()
        await self.session.refresh(msg)
        return msg

    async def get_by_conversation(self, conversation_id: UUID) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete_by_conversation(self, conversation_id: UUID) -> None:
        await self.session.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        await self.session.flush()

    async def get_window(
        self,
        conversation_id: UUID,
        max_turns: int = 15,
    ) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(max_turns * 2)
        )

        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def count(self, conversation_id: UUID) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        return result.scalar_one()
