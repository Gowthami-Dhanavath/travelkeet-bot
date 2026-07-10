"""Chat endpoints wired to Day 11 AgentOrchestrator + Day 16 safety."""
import logging
import time

from fastapi import APIRouter, HTTPException, Request, Response
from sse_starlette.sse import EventSourceResponse

from app.api.v1.schemas import ChatRequest, ChatResponse
from app.core.exceptions import ValidationError
from app.core.rate_limit import CHAT_LIMIT, limiter
from app.db.repositories.conversations import ConversationRepo
from app.db.repositories.messages import MessageRepo
from app.db.session import AsyncSessionLocal
from app.deps import OrchestratorDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["chat"])

MAX_USER_TURNS_PER_CONVERSATION = 25


async def _check_turn_cap(session_id: str) -> None:
    """Raise 429 if this conversation already has >= MAX user turns.

    Runs its own DB session — the orchestrator's session isn't open yet.
    """
    async with AsyncSessionLocal() as db:
        conv_repo = ConversationRepo(db)
        msg_repo = MessageRepo(db)
        conv = await conv_repo.get_by_session_id(session_id)
        if conv is None:
            return  # new conversation; not at cap
        user_turns = await msg_repo.count_by_role(conv.id, role="user")
        if user_turns >= MAX_USER_TURNS_PER_CONVERSATION:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "turn_cap_exceeded",
                    "message": (
                        f"This conversation has reached the "
                        f"{MAX_USER_TURNS_PER_CONVERSATION}-turn limit. "
                        f"Please start a new session."
                    ),
                },
            )


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(CHAT_LIMIT)
async def chat(
    request: Request,
    response: Response,
    req: ChatRequest,
    orch: OrchestratorDep,
) -> ChatResponse:
    start = time.perf_counter()

    if not req.message or not req.message.strip():
        raise ValidationError("Message cannot be empty.")

    await _check_turn_cap(req.session_id)

    try:
        result = await orch.handle_message(
            session_id=req.session_id,
            user_message=req.message,
            history=[],
        )
        reply = result.get("reply", "")
        conversation_id = result.get("conversation_id")
        message_id = result.get("message_id")
        tool_calls = result.get("tool_calls") or []
        slots = result.get("slots") or {}
        if isinstance(tool_calls, dict):
            tool_calls = [tool_calls]

        return ChatResponse(
            reply=reply,
            conversation_id=str(conversation_id),
            message_id=str(message_id),
            tool_calls=tool_calls,
            slots=slots if isinstance(slots, dict) else {},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat endpoint crashed: %s", str(e))
        raise
    finally:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info("Chat turn completed", extra={"latency_ms": latency_ms})


@router.post("/chat/stream")
@limiter.limit(CHAT_LIMIT)
async def chat_stream(
    request: Request,
    req: ChatRequest,
    orch: OrchestratorDep,
):
    """Server-Sent Events stream of the assistant's reply.

    Wire format:
      data: <token>
      data: <token>
      ...
      data: [DONE]
    """
    if not req.message or not req.message.strip():
        raise ValidationError("Message cannot be empty.")

    await _check_turn_cap(req.session_id)

    async def event_generator():
        try:
            async for token in orch.stream_message(req.session_id, req.message):
                yield {"data": token}
            yield {"data": "[DONE]"}
        except Exception as e:
            logger.exception("Stream failed")
            yield {"data": f"[ERROR] {str(e)}"}

    return EventSourceResponse(event_generator())