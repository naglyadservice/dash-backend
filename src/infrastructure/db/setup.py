from typing import AsyncGenerator, AsyncIterable

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.main.config import DbConfig


async def get_async_engine(config: DbConfig) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(config.build_dsn())

    yield engine

    await engine.dispose()


def get_async_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine)


async def get_async_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterable[AsyncSession]:
    async with sessionmaker() as session:
        yield session
