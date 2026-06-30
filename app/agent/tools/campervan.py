import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.repositories import CampervanRepo


SEARCH_CAMPERVANS_DECLARATION = {
    "name": "search_campervans",
    "description": "Search campervan inventory by city, capacity, price, features.",
    "parameters": {
        "type": "object",
        "properties": {
            "pickup_city": {"type": "string"},
            "min_capacity": {"type": "integer"},
            "max_price": {"type": "integer"},
            "features": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["pickup_city"],
    },
}


async def search_campervans(
    *,
    conversation_id: uuid.UUID,
    pickup_city: str,
    min_capacity: int = 2,
    max_price: int | None = None,
    features: list[str] | None = None,
) -> dict:

    async with AsyncSessionLocal() as session:
        repo = CampervanRepo(session)

        vans = await repo.search(
            base_city=pickup_city,
            min_capacity=min_capacity,
            max_price=max_price,
            features_any=features,
        )

    return {
        "query": {
            "pickup_city": pickup_city,
            "min_capacity": min_capacity,
            "max_price": max_price,
            "features": features or [],
        },
        "count": len(vans),
        "vans": [
            {
                "id": v.id,
                "name": v.name,
                "capacity": v.capacity,
                "price_per_day": v.price_per_day,
                "base_city": v.base_city,
                "features": list(v.features or []),
                "description": v.description,
            }
            for v in vans
        ],
    }