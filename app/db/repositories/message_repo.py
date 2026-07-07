from app.db.models import Message

class MessageRepo:
    def __init__(self, db):
        self.db = db

    async def append(self, conversation_id, role, content, model=None, latency_ms=None):
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            latency_ms=latency_ms,
        )

        self.db.add(msg)
        await self.db.flush()
        return msg
        
