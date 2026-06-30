from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Package


class PackageRepo:
    def __init__(self, session):
        self.session = session

    async def search_by_name_or_destination(self, query: str):
        like = f"%{query}%"
        result = await self.session.execute(
            select(Package)
            .where(Package.is_active.is_(True))
            .where(
                or_(
                    Package.name.ilike(like),
                    Package.destination.ilike(like),
                )
            )
        )
        return list(result.scalars().all())

    async def get(self, package_id: str):
        return await self.session.get(Package, package_id)

    async def upsert_many(self, packages: list[dict]) -> int:
        if not packages:
            return 0

        stmt = insert(Package).values(packages)

        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in Package.__table__.columns
            if c.name != "id"
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=update_cols,
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount or 0