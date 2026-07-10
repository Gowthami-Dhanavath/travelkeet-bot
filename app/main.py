"""FastAPI application factory."""
import asyncio
import logging
import sys
import time
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.api.admin.health import router as admin_health_router
from app.api.admin.leads import router as admin_leads_router
from app.api.admin.metrics import router as admin_metrics_router
from app.api.admin.sync import router as admin_sync_router
from app.api.v1.chat import router as chat_router
from app.api.v1.embed import router as embed_router
from app.config import settings
from app.core.anti_flood import AntiFloodMiddleware
from app.core.breaker import BreakerState, groq_breaker
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.core.rate_limit import limiter, rate_limit_handler
from app.db.session import AsyncSessionLocal
from app.integrations.groq import GroqClient


REPO_ROOT = Path(__file__).resolve().parent.parent
WIDGET_DIR = REPO_ROOT / "widget"


def _init_sentry():
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        integrations=[StarletteIntegration(), FastApiIntegration()],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=False,
    )


async def _check_db() -> dict:
    start = time.perf_counter()
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(text("SELECT 1"))
        return {"ok": True, "latency_ms": int((time.perf_counter() - start) * 1000)}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


async def _check_groq() -> dict:
    if groq_breaker.state == BreakerState.OPEN:
        return {"ok": False, "error": "breaker_open"}
    start = time.perf_counter()
    try:
        client = GroqClient()
        await client.generate_reply("ping", model="llama-3.1-8b-instant")
        return {"ok": True, "latency_ms": int((time.perf_counter() - start) * 1000)}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


async def _check_resend() -> dict:
    if not settings.resend_api_key:
        return {"ok": False, "error": "not_configured"}
    return {"ok": True, "configured": True}


def create_app() -> FastAPI:
    configure_logging("INFO")
    logger = logging.getLogger(__name__)

    _init_sentry()

    app = FastAPI(
        title="TravelKeet Bot",
        version="1.0.0-rc1",
        description="AI trip planner for TravelKeet campervan rentals",
        debug=False,   # RC — hide tracebacks from clients
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        AntiFloodMiddleware,
        burst_limit=15,
        window_seconds=60,
        ban_seconds=3600,
    )

    # CORS: LOCKED to travelkeet.com for RC
    # Local dev falls back to "*" if ALLOWED_ORIGINS is empty in .env
    _cors_origins = settings.cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=(_cors_origins != ["*"]),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(chat_router)
    app.include_router(embed_router)
    app.include_router(admin_health_router)
    app.include_router(admin_leads_router)
    app.include_router(admin_sync_router)
    app.include_router(admin_metrics_router)

    # Serve widget/ statically at /widget/*
    if WIDGET_DIR.exists():
        app.mount(
            "/widget",
            StaticFiles(directory=str(WIDGET_DIR), html=True),
            name="widget",
        )
    else:
        logger.warning("widget/ folder not found; skipping static mount")

    @app.get("/v1/health", tags=["health"])
    async def health():
        db, groq, resend = await asyncio.gather(
            _check_db(), _check_groq(), _check_resend(),
        )
        overall_ok = db["ok"]
        return {
            "status": "ok" if overall_ok else "degraded",
            "service": "travelkeet-bot",
            "version": "1.0.0-rc1",
            "checks": {"db": db, "groq": groq, "resend": resend},
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        traceback.print_exc(file=sys.stdout)
        logger.error("Unhandled exception", exc_info=True)
        # Send to Sentry
        sentry_sdk.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An error occurred processing your request.",
                }
            },
        )

    logger.info("Application initialised (v1.0.0-rc1)")
    return app


app = create_app()