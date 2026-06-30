"""save_lead tool — captures a lead and notifies the sales team."""
import logging
import re
from datetime import date
from uuid import UUID, uuid4

from app.core.exceptions import ValidationError
from app.db.repositories import LeadRepo
from app.db.session import AsyncSessionLocal
from app.db.models import Conversation

logger = logging.getLogger(__name__)


SAVE_LEAD_DECLARATION: dict = {
    "name": "save_lead",
    "description": (
        "Save a captured lead to TravelKeet's sales team. ONLY call this "
        "after itinerary delivery + user explicitly shares contact details."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "phone": {"type": "string"},
            "email": {"type": "string"},
            "trip_summary": {"type": "object"},
            "recommended_van_id": {"type": "string"},
            "pickup_city": {"type": "string"},
            "destination_city": {"type": "string"},
            "travel_from": {"type": "string"},
            "travel_to": {"type": "string"},
            "num_people": {"type": "integer"},
            "budget_inr": {"type": "integer"},
        },
        "required": ["name", "phone", "trip_summary"],
    },
}


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _normalize_phone(phone: str) -> str:
    """Force +91 format for India numbers."""
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 10:
        return "+91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits

    return phone  # let LeadRepo validation handle invalid cases


async def save_lead(
    *,
    conversation_id: UUID,
    name: str,
    phone: str,
    trip_summary: dict,
    email: str | None = None,
    recommended_van_id: str | None = None,
    pickup_city: str | None = None,
    destination_city: str | None = None,
    travel_from: str | None = None,
    travel_to: str | None = None,
    num_people: int | None = None,
    budget_inr: int | None = None,
) -> dict:

    phone = _normalize_phone(phone)

    async with AsyncSessionLocal() as session:
        repo = LeadRepo(session)

        try:
            # 🔥 FIX: ensure conversation exists (prevents FK crash)
            conv = await session.get(Conversation, conversation_id)
            if conv is None:
                conv = Conversation(
                    id=conversation_id,
                    session_id=str(uuid4())
                )
                session.add(conv)
                await session.flush()

            lead = await repo.create(
                name=name.strip(),
                phone=phone,
                trip_summary=trip_summary,
                conversation_id=conversation_id,
                email=email,
                recommended_van_id=recommended_van_id,
                pickup_city=pickup_city,
                destination_city=destination_city,
                travel_from=_parse_date(travel_from),
                travel_to=_parse_date(travel_to),
                num_people=num_people,
                budget_inr=budget_inr,
            )

            await session.commit()

        except ValidationError as e:
            await session.rollback()
            return {"success": False, "error": e.message}

        except Exception as e:
            await session.rollback()
            logger.exception("save_lead failed")
            return {"success": False, "error": str(e)}

    logger.info(
        "Lead captured",
        extra={
            "conversation_id": str(conversation_id),
            "lead_id": str(lead.id),
        },
    )

    return {
        "success": True,
        "lead_id": str(lead.id),
        "name": lead.name,
        "phone": lead.phone,
        "status": lead.status,
        "message": "Lead captured successfully. Sales team will contact you soon.",
    }