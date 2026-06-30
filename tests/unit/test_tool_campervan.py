import uuid
import pytest

from app.agent.tools.campervan import (
    SEARCH_CAMPERVANS_DECLARATION,
    search_campervans,
)


def test_declaration_exists():
    assert SEARCH_CAMPERVANS_DECLARATION["name"] == "search_campervans"
    assert "parameters" in SEARCH_CAMPERVANS_DECLARATION
    assert "pickup_city" in SEARCH_CAMPERVANS_DECLARATION["parameters"]["properties"]


@pytest.mark.asyncio
async def test_tool_returns_structure():
    result = await search_campervans(
        conversation_id=uuid.uuid4(),
        pickup_city="Mumbai",
    )

    assert isinstance(result, dict)
    assert "vans" in result
    assert "count" in result
    assert isinstance(result["vans"], list)


@pytest.mark.asyncio
async def test_tool_zero_results():
    result = await search_campervans(
        conversation_id=uuid.uuid4(),
        pickup_city="Atlantis",
    )

    assert result["count"] == 0
    assert result["vans"] == []


@pytest.mark.asyncio
async def test_tool_capacity_filter():
    result = await search_campervans(
        conversation_id=uuid.uuid4(),
        pickup_city="Delhi",
        min_capacity=6,
    )

    for v in result["vans"]:
        assert v["capacity"] >= 6