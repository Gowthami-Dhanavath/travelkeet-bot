"""Chat endpoints. Uses AgentOrchestrator interface."""

import logging
import time

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.schemas import ChatRequest, ChatResponse
from app.core.exceptions import ValidationError
from app.core.rate_limit import CHAT_LIMIT, limiter
from app.deps import ConvRepoDep, MsgRepoDep, OrchestratorDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(CHAT_LIMIT)
async def chat(
    request: Request,
    response: Response,
    req: ChatRequest,
    conv_repo: ConvRepoDep,
    msg_repo: MsgRepoDep,
    orch: OrchestratorDep,
) -> ChatResponse:
    """Send a message to the agent."""

    start = time.perf_counter()

    if not req.message or not req.message.strip():
        raise ValidationError("Message cannot be empty.")

    conv = await conv_repo.get_or_create(
        session_id=req.session_id
    )

    logger.info(
        "Chat turn received",
        extra={
            "session_id": req.session_id,
            "conversation_id": str(conv.id),
            "message_len": len(req.message),
        },
    )

    await msg_repo.append(
        conversation_id=conv.id,
        role="user",
        content=req.message,
    )

    agent_response = await orch.handle_message(
        req.session_id,
        req.message,
    )

    logger.info(
        "Chat turn completed",
        extra={
            "conversation_id": str(agent_response.conversation_id),
            "message_id": str(agent_response.message_id),
            "latency_ms": int(
                (time.perf_counter() - start) * 1000
            ),
        },
    )

    return ChatResponse(
        reply=agent_response.text,
        conversation_id=agent_response.conversation_id,
        message_id=agent_response.message_id,
    )