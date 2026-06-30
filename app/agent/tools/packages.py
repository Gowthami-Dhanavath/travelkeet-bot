from uuid import UUID
from app.db.repositories import PackageRepo
from app.db.session import AsyncSessionLocal


GET_PACKAGE_DETAILS_DECLARATION = {
    "name": "get_package_details",
    "description": "Fetch travel package details by name or destination",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    }
}


async def get_package_details(*, conversation_id: UUID, query: str):
    async with AsyncSessionLocal() as session:
        repo = PackageRepo(session)
        packages = await repo.search_by_name_or_destination(query)

    return {
        "query": query,
        "count": len(packages),
        "packages": [
            {
                "id": p.id,
                "name": p.name,
                "destination": p.destination,
                "price_inr": p.price_inr,
                "duration_days": p.duration_days,
            }
            for p in packages
        ]
    }