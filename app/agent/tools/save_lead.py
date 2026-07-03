from app.agent.tools.base import ToolRegistry

DECLARATION = {
    "name": "save_lead",
    "description": "Save a potential customer's contact details and trip interest as a lead.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Full name of the customer."},
            "phone": {"type": "string", "description": "Phone number of the customer."},
            "email": {"type": "string", "description": "Email address of the customer."},
            "trip_summary": {"type": "object", "description": "Structured trip preferences and context."},
            "recommended_van_id": {"type": "string", "description": "Recommended campervan ID."},
            "pickup_city": {"type": "string", "description": "Pickup or origin city."},
            "destination_city": {"type": "string", "description": "Destination city."},
            "travel_from": {"type": "string", "description": "Start date in YYYY-MM-DD format."},
            "travel_to": {"type": "string", "description": "End date in YYYY-MM-DD format."},
            "num_people": {"type": "integer", "description": "Number of travellers."},
            "budget_inr": {"type": "integer", "description": "Budget in INR."},
        },
        "required": ["name", "phone"],
    },
}

async def handle_save_lead(args: dict) -> dict:
    return {
        "success": False,
        "error": "save_lead requires the request-scoped tool executor.",
    }

ToolRegistry.register(DECLARATION, handle_save_lead)
