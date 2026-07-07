"""Integration tests for /admin/* API key authentication."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.security import generate_key, hash_key
from app.db.models import ApiKey
from app.main import app


@pytest.mark.asyncio
async def test_admin_endpoint_rejects_missing_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/admin/whoami")
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_admin_endpoint_rejects_malformed_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/whoami",
            headers={"Authorization": "Basic abc123"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoint_rejects_unknown_key():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/whoami",
            headers={"Authorization": "Bearer tk_definitely_not_a_real_key"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoint_accepts_valid_key(db):
    # create a key via the same code path the CLI uses
    plaintext, digest = generate_key()
    db.add(ApiKey(name="test-key-1", key_hash=digest, scopes=["admin"]))
    await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/whoami",
            headers={"Authorization": f"Bearer {plaintext}"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["key_name"] == "test-key-1"
    assert body["scopes"] == ["admin"]


@pytest.mark.asyncio
async def test_admin_endpoint_rejects_revoked_key(db):
    from datetime import datetime, timezone
    plaintext, digest = generate_key()
    key = ApiKey(
        name="revoked-key",
        key_hash=digest,
        scopes=["admin"],
        revoked_at=datetime.now(timezone.utc),
    )
    db.add(key)
    await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/admin/whoami",
            headers={"Authorization": f"Bearer {plaintext}"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_hash_key_is_deterministic():
    assert hash_key("same input") == hash_key("same input")
    assert hash_key("a") != hash_key("b")


@pytest.mark.asyncio
async def test_admin_updates_last_used_at(db):
    plaintext, digest = generate_key()
    db.add(ApiKey(name="lastused-key", key_hash=digest, scopes=["admin"]))
    await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get(
            "/admin/whoami",
            headers={"Authorization": f"Bearer {plaintext}"},
        )

    refreshed = (await db.execute(
        select(ApiKey).where(ApiKey.key_hash == digest)
    )).scalar_one()
    assert refreshed.last_used_at is not None
