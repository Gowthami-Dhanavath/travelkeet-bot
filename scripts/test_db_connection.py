# save as scripts/test_db_connection.py
import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/travelkeet")
    version = await conn.fetchval("SELECT version()")
    print("Connected:", version)
    await conn.close()

asyncio.run(main())
