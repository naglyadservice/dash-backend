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
