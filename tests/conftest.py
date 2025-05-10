from typing import AsyncIterable
from unittest.mock import Mock

import pytest
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from dash.infrastructure.auth.token_processor import JWTTokenProcessor
from dash.main.app import get_app
from dash.main.di import setup_di
from dash.models.admin_user import AdminRole, AdminUser
from dash.models.base import Base
from tests.environment import TestEnvironment


@pytest.fixture(scope="function")
async def create_tables(di_container: AsyncContainer):
    engine = await di_container.get(AsyncEngine)

    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    yield

    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()


@pytest.fixture(scope="session")
async def di_container() -> AsyncIterable[AsyncContainer]:
    from dash.main.config import Config

    container = setup_di(Config())
    yield container
    await container.close()


@pytest.fixture(scope="function")
async def request_di_container(
    di_container: AsyncContainer,
) -> AsyncIterable[AsyncContainer]:
    mock_request = Mock(spec=Request)
    mock_request.headers = {"Authorization": "Bearer test_token"}
    async with di_container(context={Request: mock_request}) as request_container:
        yield request_container


@pytest.fixture(scope="session")
async def app(di_container: AsyncContainer) -> FastAPI:
    app = get_app()
    setup_dishka(di_container, app)
    return app


@pytest.fixture(scope="session")
async def client(app: FastAPI) -> AsyncIterable[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def test_env(request_di_container: AsyncContainer):
    test_env = TestEnvironment()
    await test_env.create_test_env(request_di_container)
    yield test_env


async def auth_user_factory(
    role: AdminRole, request_di_container: AsyncContainer, mocker: Mock
):
    db_session = await request_di_container.get(AsyncSession)
    token_processor = await request_di_container.get(JWTTokenProcessor)

    user = AdminUser(
        name="Test Auth User",
        email="test_auth_user@test.com",
        password_hash="test",
        role=role,
    )
    db_session.add(user)
    await db_session.commit()

    mocker.patch.object(token_processor, "validate_access_token", return_value=user.id)

    return user


@pytest.fixture
async def user(
    request,
    request_di_container: AsyncContainer,
    test_env: TestEnvironment,
    mocker: Mock,
) -> AdminUser:
    token_processor = await request_di_container.get(JWTTokenProcessor)

    if request.param == "superadmin":
        user = test_env.superadmin
    elif request.param == "company_owner":
        user = test_env.company_owner
    elif request.param == "company_owner_1":
        user = test_env.company_owner_1
    elif request.param == "location_admin":
        user = test_env.location_admin
    elif request.param == "location_admin_1":
        user = test_env.location_admin_1
    else:
        raise ValueError(f"Invalid role: {request.param}")

    mocker.patch.object(token_processor, "validate_access_token", return_value=user.id)
    return user
