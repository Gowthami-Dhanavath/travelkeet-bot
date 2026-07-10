"""FastAPI application factory."""
import logging
import sys
import traceback
import asyncio
import time
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.v1.chat import router as chat_router
from app.api.admin.health import router as admin_health_router
from app.api.admin.leads import router as admin_leads_router
from app.config import settings
from sqlalchemy import text

from app.core.breaker import groq_breaker, BreakerState
from app.db.session import AsyncSessionLocal
from app.integrations.groq import GroqClient
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.core.rate_limit import limiter, rate_limit_handler
from app.api.admin.sync import router as admin_sync_router
from app.api.admin.metrics import router as admin_metrics_router


from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
# Setup logger globally so helper functions can access it
logger = logging.getLogger(__name__)

async def _check_db() -> dict:
    start = time.perf_counter()
    try:
        async with AsyncSessionLocal() as s:
            await s.execute(text("SELECT 1"))
        return {
            "ok": True,
            "latency_ms": int((time.perf_counter() - start) * 1000),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": type(e).__name__,
        }


async def _check_groq() -> dict:
    if groq_breaker.state == BreakerState.OPEN:
        return {
            "ok": False,
            "error": "breaker_open",
        }

    start = time.perf_counter()
    try:
        client = GroqClient()
        await client.generate_reply(
            "ping",
            model="llama-3.1-8b-instant",
        )
        return {
            "ok": True,
            "latency_ms": int((time.perf_counter() - start) * 1000),
        }
    except Exception as e:
        return {
            "ok": False,
            "error": type(e).__name__,
        }


async def _check_resend() -> dict:
    if not settings.resend_api_key:
        return {
            "ok": False,
            "error": "not_configured",
        }
    return {
        "ok": True,
        "configured": True,
    }



def _init_sentry():
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        traces_sample_rate=0.1,       # 10% of requests traced for perf
        profiles_sample_rate=0.1,
        send_default_pii=False,       # Don't leak user text
    )

def create_app() -> FastAPI:
    configure_logging("INFO")
    _init_sentry()
    # ✅ DEBUG ENABLED (safe for now)
    app = FastAPI(
        title="TravelKeet Bot",
        version="0.1.0",
        description="AI trip planner for TravelKeet campervan rentals",
        debug=True,   # 🔥 IMPORTANT
    )
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(RequestIdMiddleware)
    from app.core.anti_flood import AntiFloodMiddleware
    app.add_middleware(
        AntiFloodMiddleware,
        burst_limit=15,
        window_seconds=60,
        ban_seconds=3600,
    )
    
    _cors_origins = settings.cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=(_cors_origins != ["*"]),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    register_exception_handlers(app)

    # Include Routers
    app.include_router(chat_router)
    app.include_router(admin_health_router)
    app.include_router(admin_leads_router)
    app.include_router(admin_sync_router)
    app.include_router(admin_metrics_router)
    # Health Route
    @app.get("/v1/health", tags=["health"])
    async def health():
        db, groq, resend = await asyncio.gather(
            _check_db(),
            _check_groq(),
            _check_resend(),
        )

        overall_ok = db["ok"]

        return {
            "status": "ok" if overall_ok else "degraded",
            "service": "travelkeet-bot",
            "version": "0.1.0",
            "checks": {
                "db": db,
                "groq": groq,
                "resend": resend,
            },
        }

    # 🔥 GLOBAL ERROR HANDLER (FORCE REAL ERROR OUTPUT)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        traceback.print_exc(file=sys.stdout)
        logger.error("Unhandled exception", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": str(exc),
                }
            },
        )

    logger.info("Application initialised")
    return app


app = create_app()