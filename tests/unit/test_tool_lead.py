import uuid
import pytest

from app.db.models import Conversation
from app.db.session import AsyncSessionLocal
from app.agent.tools.lead import save_lead


@pytest.mark.asyncio
async def test_save_lead_success():
    async with AsyncSessionLocal() as session:
        conv = Conversation(id=uuid.uuid4(), session_id=str(uuid.uuid4()))
        session.add(conv)
        await session.commit()

        conv_id = conv.id

    result = await save_lead(
        conversation_id=conv_id,
        name="Priya Sharma",
        phone="9876543210",
        trip_summary={"route": "Mumbai-Goa"},
        pickup_city="Mumbai",
        destination_city="Goa",
        travel_from="2026-12-10",
        travel_to="2026-12-15",
        num_people=4,
        budget_inr=60000,
    )

    assert result["success"] is True
    assert result["lead_id"]
    assert result["phone"] == "+919876543210"