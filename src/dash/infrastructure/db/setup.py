from typing import AsyncGenerator, AsyncIterable

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from dash.main.config import PostgresConfig


async def get_async_engine(config: PostgresConfig) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(config.build_dsn())

    yield engine

    await engine.dispose()


def get_async_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterable[AsyncSession]:
    async with sessionmaker() as session:
        yield session
