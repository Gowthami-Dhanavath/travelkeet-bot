# app/agent/schemas.py
"""Public types for the agent layer. Keep this file small — it's the
contract that the API layer (Person B) and the agent layer (Person A
or you-as-stub) both depend on. Changes require a sync.
"""
from uuid import UUID

from pydantic import BaseModel


class AgentResponse(BaseModel):
    text: str
    conversation_id: UUID
    message_id: UUID
    tokens_in: int = 0
    tokens_out: int = 0