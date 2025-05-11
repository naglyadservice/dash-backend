from sqlalchemy import Select, func
from sqlalchemy.ext.asyncio import AsyncSession

from dash.models.base import Base


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, model: Base) -> None:
        self.session.add(model)

    async def flush(self) -> None:
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def _get_count(self, query: Select) -> int:
        count_query = query.with_only_columns(func.count()).select_from(*query.froms)
        count_query._group_by_clauses = ()
        count_query._order_by_clauses = ()
        count_query._with_options = ()

        result = await self.session.execute(count_query)
        return result.scalar_one()
