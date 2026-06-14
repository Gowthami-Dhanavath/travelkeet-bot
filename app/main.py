"""FastAPI application factory."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.admin.health import router as admin_health_router
from app.api.v1.chat import router as chat_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware
from app.core.rate_limit import limiter, rate_limit_handler


def create_app() -> FastAPI:
    configure_logging("INFO")
    logger = logging.getLogger(__name__)

    app = FastAPI(
        title="TravelKeet Bot",
        version="0.1.0",
        description="AI trip planner for TravelKeet campervan rentals",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    app.add_middleware(RequestIdMiddleware)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)

    app.include_router(chat_router)
    app.include_router(admin_health_router)

    @app.get("/v1/health", tags=["health"])
    async def health():
        return {
            "status": "ok",
            "service": "travelkeet-bot",
            "version": "0.1.0",
        }

    logger.info("Application initialised")
    return app


app = create_app()