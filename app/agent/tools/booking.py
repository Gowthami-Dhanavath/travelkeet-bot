"""generate_booking_link tool — builds prefilled booking URL."""

import logging
from urllib.parse import urlencode
from uuid import UUID

logger = logging.getLogger(__name__)

BOOKING_BASE_URL = "https://travelkeet.com/book"


GENERATE_BOOKING_LINK_DECLARATION = {
    "name": "generate_booking_link",
    "description": (
        "Generate a prefilled booking URL after user confirms trip details."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "van_id": {"type": "string"},
            "pickup_city": {"type": "string"},
            "pickup_date": {"type": "string"},
            "dropoff_date": {"type": "string"},
            "num_people": {"type": "integer"},
        },
        "required": ["van_id", "pickup_city", "pickup_date", "dropoff_date"],
    },
}


async def generate_booking_link(
    *,
    conversation_id: UUID,
    van_id: str,
    pickup_city: str,
    pickup_date: str,
    dropoff_date: str,
    num_people: int = 2,
) -> dict:

    params = {
        "van": van_id,
        "pickup_city": pickup_city,
        "pickup_date": pickup_date,
        "dropoff_date": dropoff_date,
        "people": num_people,
        "ref": "ai-planner",
        "conv": str(conversation_id),
    }

    url = f"{BOOKING_BASE_URL}?{urlencode(params)}"

    logger.info(
        "generate_booking_link executed",
        extra={
            "conversation_id": str(conversation_id),
            "van_id": van_id,
        },
    )

    return {
        "url": url,
        "van_id": van_id,
        "pickup_city": pickup_city,
        "pickup_date": pickup_date,
        "dropoff_date": dropoff_date,
    }