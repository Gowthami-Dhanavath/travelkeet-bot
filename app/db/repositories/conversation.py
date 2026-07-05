from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.db.models import Conversation


class ConversationRepo:
    def __init__(self, session):
        self.session = session

    async def get_or_create(self, session_id: str):
        # 1. Try fetch first
        result = await self.session.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        conv = result.scalar_one_or_none()

        if conv:
            return conv

        # 2. Create new
        conv = Conversation(session_id=session_id)
        self.session.add(conv)

        try:
            await self.session.flush()   # push to DB
        except IntegrityError:
            # 🔥 handles race / duplicate insert
            await self.session.rollback()

            result = await self.session.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )
            return result.scalar_one()

        await self.session.refresh(conv)
        return conv
