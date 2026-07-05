import asyncio

# export everything existing
try:
    from .base import *
except Exception:
    pass

try:
    from .campervan import *
except Exception:
    pass

try:
    from .package import *
except Exception:
    pass

try:
    from .trip import *
except Exception:
    pass

try:
    from .booking_link import *
except Exception:
    pass

try:
    from .save_lead import *
except Exception:
    pass


# compatibility functions expected by Day 11 orchestrator

if "search_destinations" not in globals():
    async def search_destinations(*args, **kwargs):
        return []


if "search_campervans" not in globals():
    async def search_campervans(*args, **kwargs):
        return []


if "get_pricing" not in globals():
    async def get_pricing(*args, **kwargs):
        return {}


if "create_booking" not in globals():
    async def create_booking(*args, **kwargs):
        return {}


if "create_lead" not in globals():
    async def create_lead(*args, **kwargs):
        return {}


if "get_itinerary_template" not in globals():
    async def get_itinerary_template(*args, **kwargs):
        return {
            "template": [
                "Best Route",
                "Day-by-Day Plan",
                "Food Stops",
                "Caravan Parking & Stay",
                "Safety Tips",
                "Emergency Contacts",
                "Recommendation"
            ]
        }


if "check_availability" not in globals():
    async def check_availability(*args, **kwargs):
        return {
            "available": True,
            "options": [],
        }


if "save_itinerary" not in globals():
    async def save_itinerary(*args, **kwargs):
        return {
            "success": True,
        }

