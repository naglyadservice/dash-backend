import pytest
from dishka import AsyncContainer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dash.models.controllers.controller import Controller
from tests.environment import TestEnvironment


@pytest.mark.asyncio(loop_scope="session")
async def test_hybrid_property(
    create_tables, request_di_container: AsyncContainer, test_env: TestEnvironment
):
    assert test_env.controller.company_id == test_env.company.id

    # Test in sql expression
    db_session = await request_di_container.get(AsyncSession)
    stmt = select(Controller).where(Controller.company_id == test_env.company.id)
    result = await db_session.scalar(stmt)
    assert result == test_env.controller
