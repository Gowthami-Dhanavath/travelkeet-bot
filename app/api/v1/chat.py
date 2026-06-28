import logging
import time

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.schemas import ChatRequest, ChatResponse
from app.core.exceptions import ValidationError
from app.core.rate_limit import CHAT_LIMIT, limiter
from app.deps import ConvRepoDep, MsgRepoDep

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
):
    start = time.perf_counter()

    if not req.message or not req.message.strip():
        raise ValidationError("Message cannot be empty.")

    conv = await conv_repo.get_or_create(session_id=req.session_id)

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

    stub_reply = (
        "Thanks for your message. I'm still being wired up - "
        "the AI brain comes online tomorrow."
    )

    assistant_msg = await msg_repo.append(
        conversation_id=conv.id,
        role="assistant",
        content=stub_reply,
        model="stub",
        latency_ms=int((time.perf_counter() - start) * 1000),
    )

    logger.info(
        "Chat turn completed",
        extra={
            "conversation_id": str(conv.id),
            "message_id": str(assistant_msg.id),
            "latency_ms": int((time.perf_counter() - start) * 1000),
        },
    )

    await conv_repo.session.commit()

    return ChatResponse(
        reply=stub_reply,
        conversation_id=conv.id,
        message_id=assistant_msg.id,
    )
