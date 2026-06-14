"""Pydantic models for the public chat API.

These are the shapes Person A's orchestrator must produce/consume.
Changing them requires a coordination message — they're the contract.
"""
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=8,
        max_length=100,
        description="Stable per-browser session ID assigned by the embed script.",
    )
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="The user's message text.",
    )


class ChatResponse(BaseModel):
    reply: str = Field(description="Assistant's text reply.")
    conversation_id: UUID = Field(description="Server conversation ID for the session.")
    message_id: UUID = Field(description="ID of the assistant message; used for /feedback.")