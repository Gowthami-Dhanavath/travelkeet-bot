from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class TripSlots(BaseModel):
    source: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    travelers: Optional[int] = None
    budget: Optional[int] = None
    trip_type: Optional[str] = None


class AgentResponse(BaseModel):
    text: str
    conversation_id: UUID
    message_id: UUID
    tool_calls: list[dict] = Field(default_factory=list)
    slots: dict = Field(default_factory=dict)