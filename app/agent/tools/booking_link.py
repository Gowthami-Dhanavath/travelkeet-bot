from urllib.parse import urlencode
from app.agent.tools.base import ToolRegistry

DECLARATION = {
    "name": "generate_booking_link",
    "description": "Generate a prefilled travelkeet.com booking URL for a package.",
    "parameters": {
        "type": "object",
        "properties": {
            "package_id": {"type": "string", "description": "The package ID to book."},
            "num_travellers": {"type": "integer", "description": "Number of travellers."},
            "travel_date": {"type": "string", "description": "Travel date in YYYY-MM-DD format."},
        },
        "required": ["package_id", "num_travellers", "travel_date"],
    },
}

BASE_URL = "https://www.travelkeet.com/book"

async def handle_generate_booking_link(args: dict) -> dict:
    params = {
        "package": args["package_id"],
        "travellers": args["num_travellers"],
        "date": args["travel_date"],
        "source": "ai_agent",
    }
    url = f"{BASE_URL}?{urlencode(params)}"
    return {
        "booking_url": url,
        "message": f"Here is your booking link for package {args['package_id']}!",
    }

ToolRegistry.register(DECLARATION, handle_generate_booking_link)
