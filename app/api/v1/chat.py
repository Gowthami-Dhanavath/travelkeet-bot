"""Chat endpoints wired to Day 11 AgentOrchestrator."""

import logging
import time

from fastapi import APIRouter, Request, Response
from sse_starlette.sse import EventSourceResponse
from app.api.v1.schemas import ChatRequest, ChatResponse
from app.core.exceptions import ValidationError
from app.core.rate_limit import CHAT_LIMIT, limiter
from app.deps import OrchestratorDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(CHAT_LIMIT)
async def chat(
    request: Request,
    response: Response,
    req: ChatRequest,
    orch: OrchestratorDep,
) -> ChatResponse:

    start = time.perf_counter()

    # -------------------------
    # VALIDATION
    # -------------------------
    if not req.message or not req.message.strip():
        raise ValidationError("Message cannot be empty.")

    try:
        # -------------------------
        # ORCHESTRATOR CALL
        # -------------------------
        result = await orch.handle_message(
            session_id=req.session_id,
            user_message=req.message,
            history=[],
        )

        # -------------------------
        # NORMALIZE OUTPUT SAFELY
        # -------------------------
        reply = result.get("reply", "")

        conversation_id = result.get("conversation_id")
        message_id = result.get("message_id")

        tool_calls = result.get("tool_calls") or []
        slots = result.get("slots") or {}

        # Ensure tool_calls is always JSON-safe list
        if isinstance(tool_calls, dict):
            tool_calls = [tool_calls]

        # -------------------------
        # RESPONSE BUILD
        # -------------------------
        return ChatResponse(
            reply=reply,
            conversation_id=str(conversation_id),
            message_id=str(message_id),
            tool_calls=tool_calls,
            slots=slots if isinstance(slots, dict) else {},
        )

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
    """
    Server-Sent Events streaming endpoint.

    Streams tokens produced by AgentOrchestrator.stream_message().
    """

    if not req.message or not req.message.strip():
        raise ValidationError("Message cannot be empty.")

    async def event_generator():
        try:
            async for token in orch.stream_message(
                session_id=req.session_id,
                user_message=req.message,
            ):
                yield {
                    "event": "token",
                    "data": token,
                }

            yield {
                "event": "done",
                "data": "{}",
            }

        except Exception as exc:
            logger.exception("Streaming endpoint failed")

            yield {
                "event": "error",
                "data": str(exc),
            }

    return EventSourceResponse(event_generator())
