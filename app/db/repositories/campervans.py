"""Repository for the campervans table.

This table is a cache of inventory synced from the main TravelKeet site
(Day 10 builds the sync job). Person A's search_campervans tool reads it.
"""
from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Campervan


class CampervanRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, van_id: str) -> Campervan | None:
        return await self.session.get(Campervan, van_id)

    async def search(
        self,
        *,
        base_city: str | None = None,
        min_capacity: int | None = None,
        max_price_per_day: int | None = None,
        features_any: list[str] | None = None,
        limit: int = 20,
    ) -> list[Campervan]:
        """Filter vans. None means no filter on that dimension."""
        conditions = [Campervan.is_active.is_(True)]
        if base_city:
            conditions.append(Campervan.base_city.ilike(base_city))
        if min_capacity is not None:
            conditions.append(Campervan.capacity >= min_capacity)
        if max_price_per_day is not None:
            conditions.append(Campervan.price_per_day <= max_price_per_day)
        if features_any:
            # array overlap operator: any matching feature satisfies the filter
            conditions.append(Campervan.features.op("&&")(features_any))

        stmt = (
            select(Campervan)
            .where(and_(*conditions))
            .order_by(Campervan.price_per_day.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_many(self, vans: list[dict]) -> int:
        """Bulk insert-or-update, used by the daily sync (Day 10).

        Each dict must include 'id' as the primary key.
        Returns rows affected.
        """
        if not vans:
            return 0

        stmt = insert(Campervan).values(vans)
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in Campervan.__table__.columns
            if c.name != "id"
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=update_cols,
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0

    async def deactivate_missing(self, current_ids: set[str]) -> int:
        """Mark any van not in current_ids as inactive — for sync cleanup."""
        from sqlalchemy import update
        stmt = (
            update(Campervan)
            .where(Campervan.id.notin_(current_ids))
            .where(Campervan.is_active.is_(True))
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0