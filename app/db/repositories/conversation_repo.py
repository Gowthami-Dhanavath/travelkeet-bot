from sqlalchemy import select
from app.db.models import Conversation

class ConversationRepo:
    def __init__(self, db):
        self.db = db

    async def get_or_create(self, session_id: str):
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.session_id == session_id
            )
        )
        conv = result.scalar_one_or_none()

        if conv:
            return conv

        conv = Conversation(session_id=session_id)

        self.db.add(conv)
        await self.db.flush()   # IMPORTANT: ensures ID is generated

        return conv
        