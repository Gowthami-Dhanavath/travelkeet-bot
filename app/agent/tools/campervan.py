"""search_campervans tool (copied from repo layer)"""

from uuid import UUID
from app.db.repositories import CampervanRepo
from app.db.session import AsyncSessionLocal

SEARCH_CAMPERVANS_DECLARATION = {
    "name": "search_campervans",
    "description": "Search available campervans by city, budget, or type.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    }
}

async def search_campervans(*, conversation_id: UUID, query: str):
    async with AsyncSessionLocal() as session:
        repo = CampervanRepo(session)
        vans = await repo.search(query)

    return {
        "query": query,
        "count": len(vans),
        "results": [
            {
                "id": v.id,
                "name": v.name,
                "price_per_day": v.price_per_day
            }
            for v in vans
        ]
}
