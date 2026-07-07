"""FastAPI dependency providers."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.orchestrator import AgentOrchestrator
from app.agent.tools.registry import build_registry
from app.core.security import require_api_key
from app.db.models import ApiKey
from app.db.repositories import (
    CampervanRepo,
    ConversationRepo,
    LeadRepo,
    MessageRepo,
)
from app.db.session import get_db_session
from app.integrations.groq import GroqClient


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_conversation_repo(db: DbSession) -> ConversationRepo:
    return ConversationRepo(db)


async def get_message_repo(db: DbSession) -> MessageRepo:
    return MessageRepo(db)


async def get_lead_repo(db: DbSession) -> LeadRepo:
    return LeadRepo(db)


async def get_campervan_repo(db: DbSession) -> CampervanRepo:
    return CampervanRepo(db)


ConvRepoDep = Annotated[
    ConversationRepo,
    Depends(get_conversation_repo),
]

MsgRepoDep = Annotated[
    MessageRepo,
    Depends(get_message_repo),
]

LeadRepoDep = Annotated[
    LeadRepo,
    Depends(get_lead_repo),
]

VanRepoDep = Annotated[
    CampervanRepo,
    Depends(get_campervan_repo),
]


@lru_cache(maxsize=1)
def get_groq_model():
    return GroqClient()


async def get_orchestrator(
    conv_repo: ConvRepoDep,
    msg_repo: MsgRepoDep,
    lead_repo: LeadRepoDep,
):
    return AgentOrchestrator(
        client=get_groq_model(),
        conv_repo=conv_repo,
        msg_repo=msg_repo,
        tools=build_registry(lead_repo=lead_repo),
    )


OrchestratorDep = Annotated[
    AgentOrchestrator,
    Depends(get_orchestrator),
]


AdminKey = Annotated[
    ApiKey,
    Depends(require_api_key),
]
