"""Rate limit configuration for public endpoints.

Uses SlowAPI with in-memory storage. For multi-instance prod (Day 23+),
swap the storage backend to Redis. For Day 14 launch, in-memory per
instance is fine — Railway's first instance is sticky-routed by IP anyway.
"""
import logging

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.middleware import request_id_ctx

logger = logging.getLogger(__name__)


def _client_key(request: Request) -> str:
    """Per-IP keying. Honors X-Forwarded-For when behind Railway's proxy."""
    fwd = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return fwd or get_remote_address(request)


limiter = Limiter(
    key_func=_client_key,
    default_limits=[],
    headers_enabled=True,   # adds X-RateLimit-Limit / -Remaining response headers
)


CHAT_LIMIT = "30/day"


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return our standard error envelope on 429."""
    logger.warning(
        "Rate limit exceeded",
        extra={"path": request.url.path, "client": _client_key(request)},
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "rate_limited",
                "message": "Too many requests. Please try again later.",
                "request_id": request_id_ctx.get(),
            }
        },
    )
