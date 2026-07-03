"""Repository for the conversations table."""
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation

logger = logging.getLogger(__name__)


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
        # merge: new slots overwrite old keys, old keys persist if absent in new
        merged = {**conv.collected_slots, **new_slots}
        conv.collected_slots = merged
        conv.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        logger.info(
            "DB conversation slots written",
            extra={"conversation_id": str(conv_id), "slot_keys": list(new_slots.keys())},
        )

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
