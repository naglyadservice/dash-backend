from sqlalchemy.ext.asyncio import AsyncSession

from dash.models.base import Base


class BaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, model: Base) -> None:
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)

    async def commit(self) -> None:
        await self.session.commit()
