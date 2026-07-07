import asyncio
from app.db.session import AsyncSessionLocal
from app.db.repositories import ConversationRepo, MessageRepo


async def test():
    async with AsyncSessionLocal() as session:
        conv_repo = ConversationRepo(session)
        msg_repo = MessageRepo(session)

        conv = await conv_repo.get_or_create("smoke-test")

        await msg_repo.append(conv.id, "user", "hello")
        await msg_repo.append(conv.id, "assistant", "hi")

        msgs = await msg_repo.get_window(conv.id)

        print("Messages:", [m.content for m in msgs])


asyncio.run(test())
