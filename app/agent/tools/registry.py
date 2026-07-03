import inspect
import logging
from datetime import date
from uuid import UUID

from app.agent import tools
from app.agent.tools.base import ToolRegistry as RegisteredTools
from app.db.models import Package
from app.db.repositories import LeadRepo

logger = logging.getLogger(__name__)


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


class ToolRegistry:
    def __init__(self, lead_repo: LeadRepo | None = None):
        self.lead_repo = lead_repo

    def get(self, name: str):
        try:
            return RegisteredTools.get_handler(name)
        except ValueError:
            return getattr(tools, name, None)

    def names(self):
        names = set(RegisteredTools._tools.keys())
        names.update(
            name
            for name in dir(tools)
            if not name.startswith("_") and callable(getattr(tools, name))
        )
        return list(names)

    def declarations(self) -> list[dict]:
        return RegisteredTools.get_all_declarations()

    async def execute(self, name: str, args: dict, conversation_id: str):
        logger.info(
            "Executing tool",
            extra={"tool_name": name, "conversation_id": conversation_id},
        )

        if name == "save_lead" and self.lead_repo is not None:
            return await self._save_lead(args, conversation_id)
        if name == "get_package_details" and self.lead_repo is not None:
            return await self._get_package_details(args)
        if name == "estimate_trip_cost" and self.lead_repo is not None:
            return await self._estimate_trip_cost(args)

        handler = self.get(name)
        if handler is None:
            raise ValueError(f"No tool registered with name '{name}'")

        result = handler(**args) if name in dir(tools) else handler(args)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def _save_lead(self, args: dict, conversation_id: str) -> dict:
        lead = await self.lead_repo.create(
            name=args["name"],
            phone=args["phone"],
            email=args.get("email"),
            conversation_id=UUID(conversation_id),
            trip_summary=args.get("trip_summary") or args,
            recommended_van_id=args.get("recommended_van_id"),
            pickup_city=args.get("pickup_city") or args.get("from_city") or args.get("source"),
            destination_city=args.get("destination_city") or args.get("to_city") or args.get("destination"),
            travel_from=_parse_date(args.get("travel_from")),
            travel_to=_parse_date(args.get("travel_to")),
            num_people=args.get("num_people") or args.get("num_adults") or args.get("travelers"),
            budget_inr=args.get("budget_inr") or args.get("budget"),
        )
        return {
            "success": True,
            "lead_id": str(lead.id),
            "message": f"Lead saved. Our team will contact {lead.name} shortly.",
        }

    async def _get_package_details(self, args: dict) -> dict:
        package = await self.lead_repo.session.get(Package, args["package_id"])
        if package is None:
            return {"success": False, "error": f"No package found with id '{args['package_id']}'"}
        return {
            "success": True,
            "package_id": package.id,
            "name": package.name,
            "destination": package.destination,
            "duration_days": package.duration_days,
            "price_inr": package.price_inr,
            "inclusions": package.inclusions,
            "itinerary": package.itinerary,
        }

    async def _estimate_trip_cost(self, args: dict) -> dict:
        package = await self.lead_repo.session.get(Package, args["package_id"])
        if package is None:
            return {"success": False, "error": f"Package '{args['package_id']}' not found."}
        num_travellers = int(args["num_travellers"])
        num_days = int(args["num_days"])
        price = int(package.price_inr or 0)
        base_cost = price * num_travellers * num_days
        taxes = round(base_cost * 0.18, 2)
        total = round(base_cost + taxes, 2)
        return {
            "success": True,
            "package_id": args["package_id"],
            "num_travellers": num_travellers,
            "num_days": num_days,
            "base_cost": base_cost,
            "taxes": taxes,
            "total_estimated_cost": total,
            "currency": "INR",
        }


def build_registry(lead_repo: LeadRepo | None = None):
    return ToolRegistry(lead_repo=lead_repo)
