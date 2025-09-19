from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, exists, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.company import Company
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.services.location.dto import ReadLocationListRequest


class LocationRepository(BaseRepository):
    async def get(self, location_id: UUID) -> Location | None:
        return await self.session.get(Location, location_id)

    async def exists(self, location_id: UUID) -> bool:
        stmt = select(exists().where(Location.id == location_id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def _get_list(
        self,
        data: ReadLocationListRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> tuple[Sequence[Location], int]:
        stmt = select(Location)

        if data.company_id is not None:
            stmt = stmt.where(Location.company_id == data.company_id)

        elif whereclause is not None:
            stmt = stmt.where(whereclause)

        paginated_stmt = (
            stmt.order_by(Location.created_at.desc())
            .offset(data.offset)
            .limit(data.limit)
        )

        paginated = (await self.session.scalars(paginated_stmt)).unique().all()
        total = await self._get_count(stmt)

        return paginated, total

    async def get_list_all(
        self, data: ReadLocationListRequest
    ) -> tuple[Sequence[Location], int]:
        return await self._get_list(data)

    async def get_list_by_owner(
        self, data: ReadLocationListRequest, user_id: UUID
    ) -> tuple[Sequence[Location], int]:
        whereclause = Location.company_id.in_(
            select(Company.id).where(Company.owner_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def get_list_by_admin(
        self, data: ReadLocationListRequest, user_id: UUID
    ) -> tuple[Sequence[Location], int]:
        whereclause = Location.id.in_(
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def delete(self, location: Location) -> None:
        await self.session.delete(location)
