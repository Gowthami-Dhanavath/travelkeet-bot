"""Rate limit configuration.

Day 5 wires the limiter but only logs violations (no enforcement).
Day 6 flips enforce=True after testing it doesn't false-positive in dev.
"""
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],   # explicit per-route limits, not global
)


def chat_rate_limit() -> str:
    """30 requests per IP per day on /v1/chat."""
    return "30/day"