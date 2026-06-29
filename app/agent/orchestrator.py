"""Stub orchestrator. Replace with the real Gemini-backed agent on Day 11.

This implementation honours the AgentOrchestrator.handle_message contract
exactly. It produces deterministic, slot-aware replies — enough to exercise
the full /v1/chat stack including persistence, slot merging, and the e2e
test harness.
"""
import logging
from uuid import UUID

from app.agent.schemas import AgentResponse
from app.db.repositories import ConversationRepo, MessageRepo

logger = logging.getLogger(__name__)


# A tiny rule-based "slot extractor" for the stub. Real version is a
# Gemini Flash-Lite call on Day 8 of Person A's track.
def _stub_extract_slots(message: str, current: dict) -> dict:
    """Cheap regex extraction so the stub feels alive. Not for production."""
    import re
    out: dict = {}
    text = message.lower()

    # cities: very crude — "mumbai to goa"
    m = re.search(r"\b(mumbai|delhi|goa|bangalore|pune|chennai|jaipur|ooty)\b.*?\b(to|→)\b.*?\b(mumbai|delhi|goa|bangalore|pune|chennai|jaipur|ooty)\b", text)
    if m:
        out["from_city"] = m.group(1).title()
        out["to_city"] = m.group(3).title()

    # adults
    m = re.search(r"\b(\d{1,2})\s*(adult|adults|people|of us|persons?)\b", text)
    if m:
        out["num_adults"] = int(m.group(1))

    # budget
    m = re.search(r"\b(\d{4,7})\s*(rs|rupees|inr|k|thousand)?\b", text)
    if m:
        n = int(m.group(1))
        if (m.group(2) or "").lower() in ("k", "thousand"):
            n *= 1000
        if 1000 <= n <= 1_000_000:
            out["budget_inr"] = n

    # food
    if "vegetarian" in text or "veg" in text:
        out["food_pref"] = "vegetarian"
    elif "vegan" in text:
        out["food_pref"] = "vegan"
    elif "non-veg" in text or "nonveg" in text:
        out["food_pref"] = "non-vegetarian"

    return out


def _stub_required_slots(slots: dict) -> list[str]:
    required = ["from_city", "to_city", "num_adults", "budget_inr", "food_pref"]
    return [k for k in required if k not in slots]


def _stub_itinerary(slots: dict) -> str:
    """Produces a placeholder itinerary with all 7 sections so the e2e
    harness assertions can pass against the stub."""
    return f"""Here is your trip plan from {slots['from_city']} to {slots['to_city']}:

**Route:** Best route is via NH48, roughly 600 km.

**Day-by-Day:**
Day 1: Departure and first leg.
Day 2: Sightseeing en route.
Day 3: Arrival and rest.

**Food stops:** Three {slots.get('food_pref', 'mixed')}-friendly options on the way.

**Parking & overnight:** Caravan-friendly stops at each overnight halt.

**Safety tips:** Drive in daylight, carry water, check tyres.

**Emergency contacts:** Police 100, ambulance 102, highway helpline 1033.

**Recommendation:** TK-NOMAD-01 fits {slots.get('num_adults', '?')} adults at your budget.
"""


class AgentOrchestrator:
    """The interface the API layer depends on.

    Real implementation on Day 11 will call Gemini 3 Flash; this stub is
    rule-based so you can develop the full stack without the LLM.
    """

    def __init__(self, conv_repo: ConversationRepo, msg_repo: MessageRepo):
        self.conv_repo = conv_repo
        self.msg_repo = msg_repo

    async def handle_message(self, session_id: str, user_message: str) -> AgentResponse:
        conv = await self.conv_repo.get_or_create(session_id=session_id)
        # The user message was already appended by the API layer in Day 4's
        # design. We re-fetch slots from DB so we work off persisted state.
        await self.conv_repo.update_slots(
            conv.id,
            _stub_extract_slots(user_message, conv.collected_slots),
        )
        # Re-read merged slots
        conv = await self.conv_repo.get_by_session_id(session_id)
        slots = conv.collected_slots

        missing = _stub_required_slots(slots)
        if missing:
            reply = (
                f"Got it. To plan well I still need: {', '.join(missing[:3])}. "
                "Tell me a couple of those."
            )
        else:
            reply = _stub_itinerary(slots)

        assistant_msg = await self.msg_repo.append(
            conversation_id=conv.id,
            role="assistant",
            content=reply,
            model="stub-orchestrator",
        )

        logger.info(
            "Stub orchestrator turn",
            extra={
                "conversation_id": str(conv.id),
                "slots_present": list(slots.keys()),
                "missing": missing,
            },
        )

        return AgentResponse(
            text=reply,
            conversation_id=conv.id,
            message_id=assistant_msg.id,
        )