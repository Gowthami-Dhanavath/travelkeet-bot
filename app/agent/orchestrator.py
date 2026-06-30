"""Stub orchestrator. Replace with real Gemini-backed agent on Day 11."""

import logging
import re

from app.agent.schemas import AgentResponse
from app.agent.tools.registry import build_registry
from app.db.models import ToolCall
from app.db.repositories import ConversationRepo, MessageRepo

logger = logging.getLogger(__name__)


def _stub_extract_slots(message: str, current: dict) -> dict:
    out = {}
    text = message.lower()

    route = re.search(
        r"(mumbai|delhi|goa|bangalore|pune|chennai|jaipur|ooty)\s*(?:to|→)\s*(mumbai|delhi|goa|bangalore|pune|chennai|jaipur|ooty)",
        text,
    )

    if route:
        out["from_city"] = route.group(1).title()
        out["to_city"] = route.group(2).title()


    adults = re.search(
        r"(\d+)\s*(adult|adults|people|persons)",
        text,
    )

    if adults:
        out["num_adults"] = int(adults.group(1))


    budget = re.search(
        r"(?:budget|rs|rupees|inr)?\s*(\d{4,7})",
        text,
    )

    if budget:
        value = int(budget.group(1))

        if value >= 1000:
            out["budget_inr"] = value


    if "vegetarian" in text or "veg" in text:
        out["food_pref"] = "vegetarian"


    return out



def _required_slots(slots):

    required = [
        "from_city",
        "to_city",
        "num_adults",
        "budget_inr",
        "food_pref",
    ]

    return [
        x for x in required
        if x not in slots
    ]



def _budget_per_day(total):

    if total is None:
        return None

    return total // 5



def _itinerary(slots, result):

    recommendation = "No matching campervan found."

    if result and result.get("count", 0):

        van = result["vans"][0]

        recommendation = (
            f"{van['name']} "
            f"({van['id']}) "
            f"₹{van['price_per_day']}/day"
        )


    return f"""
Here is your trip plan from {slots['from_city']} to {slots['to_city']}

Recommendation:
{recommendation}
"""



class AgentOrchestrator:


    def __init__(
        self,
        conv_repo: ConversationRepo,
        msg_repo: MessageRepo,
    ):

        self.conv_repo = conv_repo
        self.msg_repo = msg_repo
        self.tools = build_registry()



    async def handle_message(
        self,
        session_id: str,
        user_message: str,
    ) -> AgentResponse:


        conv = await self.conv_repo.get_or_create(
            session_id=session_id
        )


        await self.conv_repo.update_slots(
            conv.id,
            _stub_extract_slots(
                user_message,
                conv.collected_slots,
            ),
        )


        conv = await self.conv_repo.get_by_session_id(
            session_id
        )


        slots = conv.collected_slots

        missing = _required_slots(slots)

        tool_result = None


        if missing:

            reply = (
                "Got it. I still need: "
                + ", ".join(missing)
            )


        else:


            args = {
                "pickup_city": slots["from_city"],
                "min_capacity": slots["num_adults"],
                "max_price": _budget_per_day(
                    slots["budget_inr"]
                ),
            }


            tool_result = await self.tools.execute(
                "search_campervans",
                args,
                conversation_id=conv.id,
            )


            self.msg_repo.session.add(
                ToolCall(
                    conversation_id=conv.id,
                    tool_name="search_campervans",
                    arguments=args,
                    result=tool_result,
                    success=True,
                )
            )


            await self.msg_repo.session.flush()


            reply = _itinerary(
                slots,
                tool_result,
            )



        assistant_msg = await self.msg_repo.append(
            conversation_id=conv.id,
            role="assistant",
            content=reply,
            model="stub-orchestrator",
        )


        return AgentResponse(
            text=reply,
            conversation_id=conv.id,
            message_id=assistant_msg.id,
        )