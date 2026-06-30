"""estimate_trip_cost tool — deterministic cost calculation.

Ensures pricing is consistent and NOT hallucinated by the LLM.
"""

import logging
from uuid import UUID

from app.db.repositories import CampervanRepo
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# ---- Pricing constants (tunable later via config table) ----
FUEL_INR_PER_KM = 12
INSURANCE_PER_DAY = 350
SERVICE_FEE_PCT = 0.10


ESTIMATE_TRIP_COST_DECLARATION = {
    "name": "estimate_trip_cost",
    "description": (
        "Estimate total trip cost in INR using selected campervan, number "
        "of days, and total kilometres. Always call this before quoting "
        "any price to the user."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "van_id": {
                "type": "string",
                "description": "Campervan ID (e.g. TK-NOMAD-01)",
            },
            "days": {
                "type": "integer",
                "description": "Trip duration in days",
            },
            "km_total": {
                "type": "integer",
                "description": "Estimated total trip distance in km",
            },
        },
        "required": ["van_id", "days", "km_total"],
    },
}


async def estimate_trip_cost(
    *,
    conversation_id: UUID,
    van_id: str,
    days: int,
    km_total: int,
) -> dict:

    # ---------------- validation ----------------
    if not isinstance(days, int) or not isinstance(km_total, int):
        return {
            "error": "days and km_total must be integers",
            "van_id": van_id,
        }

    if days <= 0:
        return {
            "error": "days must be greater than 0",
            "van_id": van_id,
        }

    if km_total < 0:
        return {
            "error": "km_total cannot be negative",
            "van_id": van_id,
        }

    # ---------------- fetch van ----------------
    async with AsyncSessionLocal() as session:
        repo = CampervanRepo(session)
        van = await repo.get(van_id)

    if van is None:
        return {
            "error": f"Unknown campervan: {van_id}",
            "van_id": van_id,
        }

    # ---------------- cost calculation ----------------
    rental = van.price_per_day * days
    fuel = FUEL_INR_PER_KM * km_total
    insurance = INSURANCE_PER_DAY * days

    subtotal = rental + fuel + insurance
    service_fee = round(subtotal * SERVICE_FEE_PCT)
    total = subtotal + service_fee

    result = {
        "van_id": van_id,
        "van_name": van.name,
        "breakdown_inr": {
            "rental": rental,
            "fuel_estimate": fuel,
            "insurance": insurance,
            "service_fee": service_fee,
        },
        "total_inr": total,
        "notes": (
            "Fuel assumed at ₹12/km, insurance ₹350/day, service fee 10%."
        ),
    }

    # ---------------- logging ----------------
    logger.info(
        "estimate_trip_cost executed",
        extra={
            "conversation_id": str(conversation_id),
            "van_id": van_id,
            "days": days,
            "km_total": km_total,
            "total_inr": total,
        },
    )

    return result