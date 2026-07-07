"""Integration tests for CampervanRepo."""
import pytest

from app.db.repositories import CampervanRepo


@pytest.mark.asyncio
async def test_upsert_inserts_new(db):
    repo = CampervanRepo(db)
    vans = [{
        "id": "TEST-VAN-1",
        "name": "Test Van",
        "type": "compact",
        "capacity": 2,
        "price_per_day": 3000,
        "base_city": "Testville",
        "features": ["AC"],
        "is_active": True,
    }]
    count = await repo.upsert_many(vans)
    assert count == 1
    fetched = await repo.get("TEST-VAN-1")
    assert fetched is not None
    assert fetched.name == "Test Van"


@pytest.mark.asyncio
async def test_upsert_updates_existing(db):
    repo = CampervanRepo(db)
    base = [{
        "id": "TEST-VAN-2", "name": "Original", "type": "compact",
        "capacity": 2, "price_per_day": 3000, "base_city": "X",
        "features": ["AC"], "is_active": True,
    }]
    await repo.upsert_many(base)

    updated = [{
        "id": "TEST-VAN-2", "name": "Renamed", "type": "compact",
        "capacity": 2, "price_per_day": 3500, "base_city": "X",
        "features": ["AC", "fridge"], "is_active": True,
    }]
    await repo.upsert_many(updated)

    fetched = await repo.get("TEST-VAN-2")
    assert fetched.name == "Renamed"
    assert fetched.price_per_day == 3500
    assert "fridge" in fetched.features


@pytest.mark.asyncio
async def test_search_by_city_case_insensitive(db):
    repo = CampervanRepo(db)
    await repo.upsert_many([{
        "id": "CITY-TEST-1", "name": "X", "type": "c",
        "capacity": 4, "price_per_day": 5000, "base_city": "Mumbai",
        "features": ["AC"], "is_active": True,
    }])
    results_lower = await repo.search(base_city="mumbai")
    results_upper = await repo.search(base_city="MUMBAI")
    assert any(v.id == "CITY-TEST-1" for v in results_lower)
    assert any(v.id == "CITY-TEST-1" for v in results_upper)


@pytest.mark.asyncio
async def test_search_by_capacity(db):
    repo = CampervanRepo(db)
    await repo.upsert_many([
        {"id": "CAP-2", "name": "X", "type": "c", "capacity": 2,
         "price_per_day": 4000, "base_city": "CapCity",
         "features": [], "is_active": True},
        {"id": "CAP-6", "name": "Y", "type": "l", "capacity": 6,
         "price_per_day": 10000, "base_city": "CapCity",
         "features": [], "is_active": True},
    ])
    results = await repo.search(base_city="CapCity", min_capacity=4)
    ids = {v.id for v in results}
    assert "CAP-6" in ids
    assert "CAP-2" not in ids


@pytest.mark.asyncio
async def test_search_by_feature_overlap(db):
    repo = CampervanRepo(db)
    await repo.upsert_many([
        {"id": "F-1", "name": "X", "type": "c", "capacity": 2,
         "price_per_day": 4000, "base_city": "FeatCity",
         "features": ["AC", "fridge"], "is_active": True},
        {"id": "F-2", "name": "Y", "type": "c", "capacity": 2,
         "price_per_day": 4000, "base_city": "FeatCity",
         "features": ["AC"], "is_active": True},
    ])
    results = await repo.search(base_city="FeatCity", features_any=["fridge"])
    ids = {v.id for v in results}
    assert "F-1" in ids
    assert "F-2" not in ids


@pytest.mark.asyncio
async def test_search_inactive_excluded(db):
    repo = CampervanRepo(db)
    await repo.upsert_many([{
        "id": "INACTIVE-1", "name": "X", "type": "c", "capacity": 2,
        "price_per_day": 4000, "base_city": "InCity",
        "features": [], "is_active": False,
    }])
    results = await repo.search(base_city="InCity")
    assert not any(v.id == "INACTIVE-1" for v in results)


@pytest.mark.asyncio
async def test_deactivate_missing(db):
    repo = CampervanRepo(db)
    await repo.upsert_many([
        {"id": "STAY-1", "name": "X", "type": "c", "capacity": 2,
         "price_per_day": 4000, "base_city": "DZ",
         "features": [], "is_active": True},
        {"id": "GONE-1", "name": "Y", "type": "c", "capacity": 2,
         "price_per_day": 4000, "base_city": "DZ",
         "features": [], "is_active": True},
    ])
    n = await repo.deactivate_missing(current_ids={"STAY-1"})
    assert n >= 1
    stay = await repo.get("STAY-1")
    gone = await repo.get("GONE-1")
    assert stay.is_active is True
    assert gone.is_active is False
    
