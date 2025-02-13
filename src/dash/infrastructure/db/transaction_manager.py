from sqlalchemy.ext.asyncio import AsyncSession


class SATransactionManager:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()
