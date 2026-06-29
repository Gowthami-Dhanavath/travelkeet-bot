import pytest

# was @pytest.mark.skip(reason="Day 11: ...")
import pytest
@pytest.mark.asyncio
async def test_itinerary_has_required_sections(client, session_id):
    """When all slots are filled, the agent must produce a full itinerary
    with all 7 required sections per docs/03_WORKFLOWS.md §1.2.
    """
    turns = [
        "Mumbai to Goa trip",
        "4 adults vegetarian",
        "budget 60000",
    ]
    for t in turns:
        resp = await client.post("/v1/chat", json={"session_id": session_id, "message": t})
        assert resp.status_code == 200

    final_reply = resp.json()["reply"].lower()
    for section in ["route", "day", "food", "parking", "safety", "emergency", "recommend"]:
        assert section in final_reply, f"missing section: {section}"
