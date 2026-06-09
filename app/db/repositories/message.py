from app.db.models import Message


class MessageRepo:
    def __init__(self, session):
        self.session = session

    async def append(self, conversation_id: str, role: str, content: str, model=None, latency_ms=None):
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            latency_ms=latency_ms,
        )

        self.session.add(msg)

        # CRITICAL: persist immediately so tests can see it
        await self.session.commit()
        await self.session.refresh(msg)
        await self.session.flush()


        return msg