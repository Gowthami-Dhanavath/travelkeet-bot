"""Create a new admin API key.

Usage:
    python scripts/create_admin_key.py "Gowthami laptop" --scopes admin

The plaintext key is printed ONCE to stdout. Save it immediately — it's
not stored anywhere recoverable.
"""
import argparse
import asyncio
import sys

from app.core.security import generate_key, hash_key
from app.db.models import ApiKey
from app.db.session import AsyncSessionLocal


async def main():
    parser = argparse.ArgumentParser(description="Create an admin API key.")
    parser.add_argument("name", help="Human-readable label, e.g. 'Gowthami laptop'.")
    parser.add_argument(
        "--scopes",
        nargs="+",
        default=["admin"],
        help="Scopes granted to this key (default: admin).",
    )
    args = parser.parse_args()

    plaintext, digest = generate_key()

    async with AsyncSessionLocal() as session:
        try:
            row = ApiKey(name=args.name, key_hash=digest, scopes=args.scopes)
            session.add(row)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    print("=" * 60)
    print("API key created. SAVE THIS NOW — it will not be shown again.")
    print("=" * 60)
    print(f"Name:      {args.name}")
    print(f"Scopes:    {', '.join(args.scopes)}")
    print(f"Key:       {plaintext}")
    print(f"SHA-256:   {digest}")
    print("=" * 60)
    print("Add to your .env or Railway env vars as needed for testing.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(1)
        