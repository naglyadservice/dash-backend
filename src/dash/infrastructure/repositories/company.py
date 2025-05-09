from typing import Any, Sequence

from sqlalchemy import ColumnElement, exists, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.company import Company


class CompanyRepository(BaseRepository):
    async def exists(self, company_id: int) -> bool:
        stmt = select(exists().where(Company.id == company_id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get(self, company_id: int) -> Company | None:
        return await self.session.get(Company, company_id)

    async def _get_list(
        self, whereclause: ColumnElement[Any] | None = None
    ) -> Sequence[Company]:
        stmt = select(Company)
        if whereclause is not None:
            stmt = stmt.where(whereclause)

        result = await self.session.scalars(stmt)
        return result.all()

    async def get_list_all(self) -> Sequence[Company]:
        return await self._get_list()

    async def get_list_by_owner(self, owner_id: int) -> Sequence[Company]:
        whereclause = Company.owner_id == owner_id
        return await self._get_list(whereclause)
