import pytest

from app.db.repositories import ConversationRepo


@pytest.mark.asyncio
async def test_merge_preserves_existing_keys(db):
    repo = ConversationRepo(db)

    conv = await repo.get_or_create(
        session_id="merge-preserve-1"
    )

    await repo.update_slots(
        conv.id,
        {"from_city": "Mumbai"}
    )

    await repo.update_slots(
        conv.id,
        {"to_city": "Goa"}
    )

    await db.refresh(conv)

    assert conv.collected_slots == {
        "from_city": "Mumbai",
        "to_city": "Goa"
    }


@pytest.mark.asyncio
async def test_merge_overwrites_same_key(db):
    repo = ConversationRepo(db)

    conv = await repo.get_or_create(
        session_id="merge-overwrite-1"
    )

    await repo.update_slots(
        conv.id,
        {"num_adults": 4}
    )

    await repo.update_slots(
        conv.id,
        {"num_adults": 5}
    )

    await db.refresh(conv)

    assert conv.collected_slots["num_adults"] == 5


@pytest.mark.asyncio
async def test_empty_update_keeps_old_data(db):
    repo = ConversationRepo(db)

    conv = await repo.get_or_create(
        session_id="merge-empty-1"
    )

    await repo.update_slots(
        conv.id,
        {
            "from_city": "Mumbai",
            "budget_inr": 50000
        }
    )

    await repo.update_slots(
        conv.id,
        {}
    )

    await db.refresh(conv)

    assert conv.collected_slots == {
        "from_city": "Mumbai",
        "budget_inr": 50000
    }


@pytest.mark.asyncio
async def test_merge_replaces_nested_dict(db):
    repo = ConversationRepo(db)

    conv = await repo.get_or_create(
        session_id="merge-nested-1"
    )

    await repo.update_slots(
        conv.id,
        {
            "special": {
                "pet": True,
                "elderly": True
            }
        }
    )

    await repo.update_slots(
        conv.id,
        {
            "special": {
                "wheelchair": True
            }
        }
    )

    await db.refresh(conv)

    assert conv.collected_slots["special"] == {
        "wheelchair": True
    }


@pytest.mark.asyncio
async def test_merge_null_value(db):
    repo = ConversationRepo(db)

    conv = await repo.get_or_create(
        session_id="merge-null-1"
    )

    await repo.update_slots(
        conv.id,
        {"budget": 60000}
    )

    await repo.update_slots(
        conv.id,
        {"budget": None}
    )

    await db.refresh(conv)

    assert conv.collected_slots["budget"] is None


@pytest.mark.asyncio
async def test_merge_list_replaces_previous_list(db):
    repo = ConversationRepo(db)

    conv = await repo.get_or_create(
        session_id="merge-list-1"
    )

    await repo.update_slots(
        conv.id,
        {
            "food": ["veg"]
        }
    )

    await repo.update_slots(
        conv.id,
        {
            "food": ["veg", "no garlic"]
        }
    )

    await db.refresh(conv)

    assert conv.collected_slots["food"] == [
        "veg",
        "no garlic"
    ]