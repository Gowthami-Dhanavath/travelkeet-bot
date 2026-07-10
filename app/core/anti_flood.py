"""Anti-flood middleware — bans IPs that burst-request beyond a threshold."""
import asyncio
import logging
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AntiFloodMiddleware(BaseHTTPMiddleware):
    """Rejects IPs that exceed `burst_limit` requests in `window_seconds`.

    Once flagged, the IP is banned for `ban_seconds`. This complements the
    daily rate limiter (which uses a slower window) by catching bursts.
    """

    def __init__(
        self,
        app,
        *,
        burst_limit: int = 15,
        window_seconds: int = 60,
        ban_seconds: int = 3600,
        protected_paths: tuple[str, ...] = ("/v1/chat", "/v1/chat/stream"),
    ):
        super().__init__(app)
        self.burst_limit = burst_limit
        self.window_seconds = window_seconds
        self.ban_seconds = ban_seconds
        self.protected_paths = protected_paths
        self._history: dict[str, deque] = defaultdict(deque)
        self._bans: dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _client_ip(self, request: Request) -> str:
        # Honour X-Forwarded-For (Railway proxies)
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown"

    async def dispatch(self, request: Request, call_next):
        # Only guard chat endpoints
        if not any(request.url.path.startswith(p) for p in self.protected_paths):
            return await call_next(request)

        ip = self._client_ip(request)
        now = time.monotonic()

        async with self._lock:
            # Currently banned?
            banned_until = self._bans.get(ip)
            if banned_until and banned_until > now:
                remaining = int(banned_until - now)
                logger.warning(
                    "Blocked request from banned IP",
                    extra={"ip": ip, "remaining_s": remaining, "path": request.url.path},
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "flood_ban",
                            "message": f"Too many requests. Try again in {remaining}s.",
                        }
                    },
                )
            if banned_until:
                # Expired; clear
                self._bans.pop(ip, None)

            # Track this request
            history = self._history[ip]
            history.append(now)
            # Prune old entries
            cutoff = now - self.window_seconds
            while history and history[0] < cutoff:
                history.popleft()

            # Over threshold?
            if len(history) > self.burst_limit:
                self._bans[ip] = now + self.ban_seconds
                logger.warning(
                    "IP banned for flooding",
                    extra={
                        "ip": ip,
                        "requests_in_window": len(history),
                        "window_s": self.window_seconds,
                        "ban_s": self.ban_seconds,
                    },
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "flood_ban",
                            "message": (
                                f"Flood detected: {len(history)} requests in "
                                f"{self.window_seconds}s. Banned for {self.ban_seconds}s."
                            ),
                        }
                    },
                )

        return await call_next(request)