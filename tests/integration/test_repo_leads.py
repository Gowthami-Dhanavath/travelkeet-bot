"""Integration tests for LeadRepo."""
import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.db.repositories import ConversationRepo, LeadRepo, normalize_phone


@pytest.mark.parametrize("raw, expected", [
    ("9876543210", "+919876543210"),
    ("+919876543210", "+919876543210"),
    ("+91 9876543210", "+919876543210"),
    ("+91-9876543210", "+919876543210"),
    ("91-9876543210", "+919876543210"),
    ("  9876543210  ", "+919876543210"),
])
def test_normalize_phone_valid(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("bad", [
    "",
    "12345",
    "123456789",        # 9 digits, too short
    "12345678901",      # 11 digits, wrong start
    "+1-555-555-5555",  # US number
    "1234567890",       # starts with 1
    "abcdefghij",
])
def test_normalize_phone_invalid_raises(bad):
    with pytest.raises(ValidationError):
        normalize_phone(bad)


@pytest.mark.asyncio
async def test_lead_create_minimal(db):
    conv_repo = ConversationRepo(db)
    conv = await conv_repo.get_or_create(session_id="lead-test-1")
    lead_repo = LeadRepo(db)

    lead = await lead_repo.create(
        name="Priya Sharma",
        phone="9876543210",
        trip_summary={"route": "Mumbai → Goa", "days": 5},
        conversation_id=conv.id,
    )
    assert lead.id is not None
    assert lead.name == "Priya Sharma"
    assert lead.phone == "+919876543210"
    assert lead.status == "new"
    assert lead.trip_summary["route"] == "Mumbai → Goa"


@pytest.mark.asyncio
async def test_lead_create_blank_name_rejected(db):
    lead_repo = LeadRepo(db)
    with pytest.raises(ValidationError):
        await lead_repo.create(
            name="   ",
            phone="9876543210",
            trip_summary={},
        )


@pytest.mark.asyncio
async def test_lead_status_transition_sets_contacted_at(db):
    lead_repo = LeadRepo(db)
    lead = await lead_repo.create(
        name="Test User",
        phone="9876543210",
        trip_summary={},
    )
    assert lead.contacted_at is None

    updated = await lead_repo.update_status(lead.id, status="contacted")
    assert updated.status == "contacted"
    assert updated.contacted_at is not None


@pytest.mark.asyncio
async def test_lead_invalid_status_rejected(db):
    lead_repo = LeadRepo(db)
    lead = await lead_repo.create(
        name="Test User",
        phone="9876543210",
        trip_summary={},
    )
    with pytest.raises(ValidationError):
        await lead_repo.update_status(lead.id, status="abducted-by-aliens")


@pytest.mark.asyncio
async def test_lead_get_nonexistent_raises(db):
    import uuid
    lead_repo = LeadRepo(db)
    with pytest.raises(NotFoundError):
        await lead_repo.get(uuid.uuid4())


@pytest.mark.asyncio
async def test_lead_list_by_status_filters(db):
    lead_repo = LeadRepo(db)
    for i in range(3):
        await lead_repo.create(
            name=f"User {i}",
            phone=f"98765432{i:02d}",
            trip_summary={},
        )
    # set one to contacted
    leads = await lead_repo.list_by_status(status="new")
    await lead_repo.update_status(leads[0].id, status="contacted")

    new_leads = await lead_repo.list_by_status(status="new")
    contacted = await lead_repo.list_by_status(status="contacted")
    assert len(new_leads) >= 2
    assert len(contacted) >= 1
