"""Repository for the leads table."""
import logging
import re
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.db.models import Lead

logger = logging.getLogger(__name__)


# Accepts: 9876543210, +919876543210, +91 9876543210, +91-9876543210
_PHONE_RE = re.compile(r"^(?:\+?91[\s-]?)?([6-9]\d{9})$")


def normalize_phone(raw: str) -> str:
    """Return canonical +91XXXXXXXXXX or raise ValidationError."""
    if not raw:
        raise ValidationError("Phone is required.")
    cleaned = raw.strip().replace(" ", "").replace("-", "")
    m = _PHONE_RE.match(cleaned)
    if not m:
        raise ValidationError(f"Invalid Indian mobile number: {raw}")
    return "+91" + m.group(1)


class LeadRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        *,
        name: str,
        phone: str,
        trip_summary: dict,
        conversation_id: UUID | None = None,
        email: str | None = None,
        recommended_van_id: str | None = None,
        pickup_city: str | None = None,
        destination_city: str | None = None,
        travel_from: date | None = None,
        travel_to: date | None = None,
        num_people: int | None = None,
        budget_inr: int | None = None,
    ) -> Lead:
        name = (name or "").strip()
        if not name:
            raise ValidationError("Lead name is required.")
        if len(name) > 255:
            raise ValidationError("Lead name too long.")

        canonical_phone = normalize_phone(phone)

        if email is not None:
            email = email.strip().lower() or None

        lead = Lead(
            name=name,
            phone=canonical_phone,
            email=email,
            conversation_id=conversation_id,
            trip_summary=trip_summary or {},
            recommended_van_id=recommended_van_id,
            pickup_city=pickup_city,
            destination_city=destination_city,
            travel_from=travel_from,
            travel_to=travel_to,
            num_people=num_people,
            budget_inr=budget_inr,
        )
        self.session.add(lead)
        await self.session.flush()
        logger.info(
            "DB lead written",
            extra={
                "conversation_id": str(conversation_id) if conversation_id else None,
                "lead_id": str(lead.id),
            },
        )
        return lead

    async def get(self, lead_id: UUID) -> Lead:
        lead = await self.session.get(Lead, lead_id)
        if lead is None:
            raise NotFoundError(f"Lead {lead_id} not found.")
        return lead

    async def list_by_status(
        self, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Lead]:
        stmt = select(Lead).order_by(Lead.created_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Lead.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        lead_id: UUID,
        *,
        status: str | None = None,
        assigned_to: str | None = None,
        notes: str | None = None,
    ) -> Lead:
        valid_statuses = {"new", "contacted", "qualified", "converted", "lost"}
        if status is not None and status not in valid_statuses:
            raise ValidationError(f"Invalid status: {status}")

        lead = await self.get(lead_id)
        if status is not None:
            lead.status = status
            if status == "contacted" and lead.contacted_at is None:
                lead.contacted_at = datetime.now(timezone.utc)
        if assigned_to is not None:
            lead.assigned_to = assigned_to
        if notes is not None:
            lead.notes = notes
        lead.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        return lead

    async def count_by_status(self) -> dict[str, int]:
        from sqlalchemy import func
        result = await self.session.execute(
            select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
        )
        return {row[0]: row[1] for row in result.all()}

