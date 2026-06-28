from sqlalchemy import select
from app.db.models import Conversation


class ConversationRepo:
    def __init__(self, db):
        self.db = db

    async def get_or_create(self, session_id: str) -> Conversation:
        # -------------------------
        # 1. Try fetch existing
        # -------------------------
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.session_id == session_id
            )
        )
        conv = result.scalar_one_or_none()

        if conv:
            return conv

        # -------------------------
        # 2. Create new conversation
        # -------------------------
        conv = Conversation(session_id=session_id)

        self.db.add(conv)

        # -------------------------
        # 3. IMPORTANT:
        # flush ONLY (not commit)
        # ensures:
        # - ID generation
        # - visible in same transaction
        # -------------------------
        await self.db.flush()

        return conv