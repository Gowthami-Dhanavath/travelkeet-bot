from app.agent.tools.base import ToolRegistry

DECLARATION = {
    "name": "get_package_details",
    "description": "Fetch full details of a travel package by its ID.",
    "parameters": {
        "type": "object",
        "properties": {
            "package_id": {
                "type": "string",
                "description": "The unique ID of the travel package.",
            }
        },
        "required": ["package_id"],
    },
}

async def handle_get_package_details(args: dict) -> dict:
    from app.repos.package_repo import PackageRepo
    repo = PackageRepo()
    package = await repo.get_by_id(args["package_id"])
    if not package:
        return {"error": f"No package found with id '{args['package_id']}'"}
    return {
        "package_id": package.id,
        "name": package.name,
        "destination": package.destination,
        "duration_days": package.duration_days,
        "price_per_person": package.price_per_person,
        "inclusions": package.inclusions,
        "itinerary": package.itinerary,
    }

ToolRegistry.register(DECLARATION, handle_get_package_details)
