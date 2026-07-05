from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/travelkeet",
)

# IMPORTANT: pool_pre_ping + future compatibility
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# -------------------------
# Base (if not already elsewhere)
# -------------------------
class Base(DeclarativeBase):
    pass


# -------------------------
# Dependency for FastAPI + tests
# -------------------------
async def get_db_session():
    """
    ONE session per request/test.
    CRITICAL: prevents 'different loop' asyncpg errors.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

