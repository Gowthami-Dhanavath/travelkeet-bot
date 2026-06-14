import asyncio
from app.db.session import AsyncSessionLocal
from app.db.repositories import CampervanRepo

async def main():
    async with AsyncSessionLocal() as s:
        repo = CampervanRepo(s)
        for city in ["Mumbai", "Delhi", "Bangalore", "Hyderabad"]:
            vans = await repo.search(base_city=city)
            print(f"{city}: {len(vans)} active vans")

asyncio.run(main())
