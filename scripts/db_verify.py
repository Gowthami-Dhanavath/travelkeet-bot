import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


SESSION_ID = "day11-grok-run1"


async def run():
    async with AsyncSessionLocal() as session:

        print("\n--- USER + ASSISTANT MESSAGE COUNT ---")
        q1 = text("""
            SELECT role, COUNT(*)
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE c.session_id = :sid
            GROUP BY role
        """)
        res = await session.execute(q1, {"sid": SESSION_ID})
        print(res.fetchall())

        print("\n--- TOOL CALLS SUMMARY ---")
        q2 = text("""
            SELECT tool_name, COUNT(*), SUM(CASE WHEN success THEN 1 ELSE 0 END)
            FROM tool_calls tc
            JOIN conversations c ON tc.conversation_id = c.id
            WHERE c.session_id = :sid
            GROUP BY tool_name
        """)
        res = await session.execute(q2, {"sid": SESSION_ID})
        print(res.fetchall())

        print("\n--- LEAD CHECK ---")
        q3 = text("""
            SELECT name, phone, pickup_city, destination_city
            FROM leads l
            JOIN conversations c ON l.conversation_id = c.id
            WHERE c.session_id = :sid
        """)
        res = await session.execute(q3, {"sid": SESSION_ID})
        print(res.fetchall())


asyncio.run(run())