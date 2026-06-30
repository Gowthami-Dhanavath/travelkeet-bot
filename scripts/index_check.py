import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def run_campervan_query():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
        EXPLAIN ANALYZE
        SELECT * FROM campervans
        WHERE is_active = true
        AND base_city = 'Mumbai'
        AND capacity >= 4
        ORDER BY price_per_day ASC
        LIMIT 20;
        """))

        print("\nCAMPRVAN QUERY PLAN:\n")
        for row in result:
            print(row)


async def run_conversation_query():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
        EXPLAIN ANALYZE
        SELECT * FROM conversations
        WHERE session_id = 'test-session';
        """))

        print("\nCONVERSATION QUERY PLAN:\n")
        for row in result:
            print(row)


async def main():
    await run_campervan_query()
    await run_conversation_query()


if __name__ == "__main__":
    asyncio.run(main())