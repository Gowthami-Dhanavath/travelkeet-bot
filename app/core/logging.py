"""Structured JSON logging with PII scrubbing.

Every log line is one JSON object on one line. The PII scrubber masks
Indian phone numbers and email addresses in log output BEFORE the line is
written, so even debug-level logging is safe to ship to a third-party service.
"""
import json
import logging
import re
import sys
from datetime import datetime, timezone

from app.core.middleware import request_id_ctx


# Patterns intentionally over-eager — false positives are fine, false
# negatives leak PII.
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"""(?x)
    (?<!\d)                        # not preceded by a digit
    (?:\+?91[\s-]?)?               # optional +91 country code
    [6-9]\d{9}                     # Indian mobile: starts 6-9, 10 digits
    (?!\d)
    """
)
_GENERIC_LONG_DIGITS = re.compile(r"(?<!\d)\d{10,}(?!\d)")


def scrub_pii(text: str) -> str:
    if not text:
        return text
    text = _EMAIL_RE.sub("<email>", text)
    text = _PHONE_RE.sub("<phone>", text)
    text = _GENERIC_LONG_DIGITS.sub("<num>", text)
    return text


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record, with PII scrubbed."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        scrubbed = scrub_pii(message)

        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": scrubbed,
            "request_id": request_id_ctx.get(),
        }
        # Optional extras attached via logger.info("...", extra={"key": val})
        for key, value in record.__dict__.items():
            if key in {
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno", "lineno",
                "module", "msecs", "message", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "thread", "threadName", "taskName",
            }:
                continue
            payload[key] = scrub_pii(str(value)) if isinstance(value, str) else value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Replace any existing handlers with our JSON handler."""
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Quiet down noisy libraries
    logging.getLogger("uvicorn.access").setLevel("WARNING")
    logging.getLogger("sqlalchemy.engine").setLevel("WARNING")
