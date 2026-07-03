"""Pydantic models for the public chat API.

These are the request/response contracts for the public chat endpoint.
"""

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
    reply: str = Field(
        description="Assistant's text reply."
    )

    conversation_id: str = Field(
        description="Server conversation ID for the session.",
    )

    message_id: str = Field(
        description="Assistant message ID.",
    )

    tool_calls: list[dict] = Field(
        default_factory=list,
        description="Tool calls executed by the agent.",
    )

    slots: dict = Field(
        default_factory=dict,
        description="Collected trip slots after this turn.",
    )
