import uuid
from urllib.parse import urlparse, parse_qs

import pytest

from app.agent.tools.booking import (
    BOOKING_BASE_URL,
    GENERATE_BOOKING_LINK_DECLARATION,
    generate_booking_link,
)


def test_declaration_shape():
    d = GENERATE_BOOKING_LINK_DECLARATION
    assert d["name"] == "generate_booking_link"
    assert "van_id" in d["parameters"]["required"]


@pytest.mark.asyncio
async def test_booking_url_generation():
    conv_id = uuid.uuid4()

    result = await generate_booking_link(
        conversation_id=conv_id,
        van_id="TK-NOMAD-01",
        pickup_city="Mumbai",
        pickup_date="2026-12-10",
        dropoff_date="2026-12-15",
        num_people=4,
    )

    assert result["url"].startswith(BOOKING_BASE_URL)

    parsed = urlparse(result["url"])
    qs = parse_qs(parsed.query)

    assert qs["van"] == ["TK-NOMAD-01"]
    assert qs["pickup_city"] == ["Mumbai"]
    assert qs["pickup_date"] == ["2026-12-10"]
    assert qs["dropoff_date"] == ["2026-12-15"]
    assert qs["people"] == ["4"]