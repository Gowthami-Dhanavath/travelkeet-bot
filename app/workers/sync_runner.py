import asyncio
from app.integrations.travelkeet_sync import sync_campervans

if __name__ == "__main__":
    result = asyncio.run(sync_campervans())
    print(result)