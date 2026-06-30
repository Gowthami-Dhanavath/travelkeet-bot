from uuid import UUID

from pydantic import BaseModel


class AgentResponse(BaseModel):
    text: str
    conversation_id: UUID
    message_id: UUID
