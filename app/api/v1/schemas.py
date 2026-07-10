"""API schemas for the /v1 namespace."""
import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# session_id must be safe URL-ish tokens only
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

# Control characters we reject in messages (aside from tab, newline, CR)
_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=100)
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("session_id")
    @classmethod
    def _validate_session_id(cls, v: str) -> str:
        v = v.strip()
        if not _SESSION_ID_PATTERN.match(v):
            raise ValueError(
                "session_id must contain only letters, digits, hyphens, underscores"
            )
        return v

    @field_validator("message")
    @classmethod
    def _validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty or whitespace-only")
        if _CONTROL_CHARS_PATTERN.search(v):
            raise ValueError("message contains disallowed control characters")
        return v


class ChatResponse(BaseModel):
    reply: str
    conversation_id: UUID
    message_id: UUID
    tool_calls: list[dict] = Field(default_factory=list)
    slots: dict = Field(default_factory=dict)