from app.agent.tools.base import ToolRegistry

DECLARATION = {
    "name": "estimate_trip_cost",
    "description": "Estimate the total cost of a trip given a package ID, number of travellers, and number of days.",
    "parameters": {
        "type": "object",
        "properties": {
            "package_id": {"type": "string", "description": "The travel package ID."},
            "num_travellers": {"type": "integer", "description": "Number of people travelling."},
            "num_days": {"type": "integer", "description": "Number of days for the trip."},
        },
        "required": ["package_id", "num_travellers", "num_days"],
    },
}

async def handle_estimate_trip_cost(args: dict) -> dict:
    from app.repos.package_repo import PackageRepo
    repo = PackageRepo()
    package = await repo.get_by_id(args["package_id"])
    if not package:
        return {"error": f"Package '{args['package_id']}' not found."}
    base_cost = package.price_per_person * int(args["num_travellers"]) * int(args["num_days"])
    taxes = round(base_cost * 0.18, 2)
    total = round(base_cost + taxes, 2)
    return {
        "package_id": args["package_id"],
        "num_travellers": args["num_travellers"],
        "num_days": args["num_days"],
        "base_cost": base_cost,
        "taxes": taxes,
        "total_estimated_cost": total,
        "currency": "INR",
    }

ToolRegistry.register(DECLARATION, handle_estimate_trip_cost)