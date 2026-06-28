"""Repository for the conversations table."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation


class ConversationRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_session_id(self, session_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        session_id: str,
        user_agent: str | None = None,
        ip_hash: str | None = None,
    ) -> Conversation:
        existing = await self.get_by_session_id(session_id)
        if existing:
            return existing

        conv = Conversation(
            session_id=session_id,
            user_agent=user_agent,
            ip_hash=ip_hash,
        )
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def update_slots(self, conv_id: UUID, new_slots: dict) -> None:
        conv = await self.session.get(Conversation, conv_id)
        if conv is None:
            raise ValueError(f"Conversation {conv_id} not found")

        merged = {**conv.collected_slots, **new_slots}
        conv.collected_slots = merged
        conv.updated_at = datetime.now(timezone.utc)

        await self.session.flush()

    async def update_usage(
        self, conv_id: UUID, tokens_in: int, tokens_out: int, cost_cents: int
    ) -> None:
        conv = await self.session.get(Conversation, conv_id)
        if conv is None:
            raise ValueError(f"Conversation {conv_id} not found")

        conv.total_tokens_in += tokens_in
        conv.total_tokens_out += tokens_out
        conv.cost_cents += cost_cents
        conv.updated_at = datetime.now(timezone.utc)

        await self.session.flush()