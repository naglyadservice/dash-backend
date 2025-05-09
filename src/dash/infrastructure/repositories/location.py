from typing import Any, Sequence

from sqlalchemy import ColumnElement, exists, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.company import Company
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin


class LocationRepository(BaseRepository):
    async def get(self, location_id: int) -> Location | None:
        return await self.session.get(Location, location_id)

    async def exists(self, location_id: int) -> bool:
        stmt = select(exists().where(Location.id == location_id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def _get_list(
        self, whereclause: ColumnElement[Any] | None = None
    ) -> Sequence[Location]:
        stmt = select(Location)
        if whereclause is not None:
            stmt = stmt.where(whereclause)

        result = await self.session.scalars(stmt)
        return result.all()

    async def get_list_all(self) -> Sequence[Location]:
        return await self._get_list()

    async def get_list_by_owner(self, user_id: int) -> Sequence[Location]:
        whereclause = Location.company_id.in_(
            select(Company.id).where(Company.owner_id == user_id)
        )
        return await self._get_list(whereclause)

    async def get_list_by_admin(self, user_id: int) -> Sequence[Location]:
        whereclause = Location.id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_list(whereclause)
