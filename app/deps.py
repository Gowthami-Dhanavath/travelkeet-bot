
"""FastAPI dependency providers."""
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.db.repositories import ConversationRepo, MessageRepo


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_conversation_repo(db: DbSession) -> ConversationRepo:
    return ConversationRepo(db)


async def get_message_repo(db: DbSession) -> MessageRepo:
    return MessageRepo(db)

async def get_msg_repo(session: AsyncSession):
    return MessageRepo(session)

ConvRepoDep = Annotated[ConversationRepo, Depends(get_conversation_repo)]
MsgRepoDep = Annotated[MessageRepo, Depends(get_message_repo)]
