"""Seed the local database with campervan inventory for development.

Idempotent: re-running upserts, doesn't duplicate.
Run: python scripts/seed_db.py
"""
import asyncio
import json
import sys
from pathlib import Path

from app.db.repositories import CampervanRepo
from app.db.session import AsyncSessionLocal

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = REPO_ROOT / "data" / "campervans.seed.json"


async def main():
    if not SEED_FILE.exists():
        print(f"ERROR: seed file not found at {SEED_FILE}", file=sys.stderr)
        sys.exit(1)

    vans = json.loads(SEED_FILE.read_text())
    print(f"Loaded {len(vans)} vans from seed file.")

    async with AsyncSessionLocal() as session:
        try:
            repo = CampervanRepo(session)
            affected = await repo.upsert_many(vans)
            await session.commit()
            print(f"OK: upserted {affected} rows into campervans.")
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
    