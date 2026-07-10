"""Minimal async circuit breaker for external dependencies."""
import asyncio
import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


class BreakerState(str, Enum):
    CLOSED = "closed"      # normal
    OPEN = "open"          # tripping — refuse fast
    HALF_OPEN = "half"     # trial request allowed


class CircuitBreaker:
    """Trips OPEN after N consecutive failures; cools for M seconds; then HALF_OPEN
    lets ONE trial through. Success closes; failure re-opens."""

    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int = 5,
        cooldown_seconds: int = 30,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._state = BreakerState.CLOSED
        self._failures = 0
        self._opened_at = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> BreakerState:
        if self._state == BreakerState.OPEN and time.monotonic() - self._opened_at >= self.cooldown_seconds:
            return BreakerState.HALF_OPEN
        return self._state

    async def call(self, coro_fn, *args, **kwargs):
        """Wrap a coroutine call with breaker logic."""
        current = self.state
        if current == BreakerState.OPEN:
            raise CircuitOpenError(
                f"Circuit {self.name!r} is OPEN; retry after "
                f"{self.cooldown_seconds - (time.monotonic() - self._opened_at):.0f}s"
            )

        try:
            result = await coro_fn(*args, **kwargs)
        except Exception:
            await self._record_failure()
            raise

        await self._record_success()
        return result

    async def _record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold and self._state == BreakerState.CLOSED:
                self._state = BreakerState.OPEN
                self._opened_at = time.monotonic()
                logger.warning(
                    "Circuit breaker OPENED",
                    extra={"breaker": self.name, "failures": self._failures},
                )

    async def _record_success(self) -> None:
        async with self._lock:
            if self._state != BreakerState.CLOSED:
                logger.info("Circuit breaker CLOSED", extra={"breaker": self.name})
            self._failures = 0
            self._state = BreakerState.CLOSED
            self._opened_at = 0.0


class CircuitOpenError(RuntimeError):
    """Raised when a call is refused because the breaker is OPEN."""


# Singleton breakers
groq_breaker = CircuitBreaker("groq", failure_threshold=5, cooldown_seconds=30)