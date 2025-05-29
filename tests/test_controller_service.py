from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.models.energy_state import DailyEnergyState
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    TasmotaIDAlreadyTakenError,
)
from dash.services.controller.dto import GetEnergyStatsRequest, SetupTasmotaRequest
from dash.services.controller.service import ControllerService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@pytest.mark.parametrize("user", ("superadmin",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_setup_tasmota(
    request_di_container: AsyncContainer, test_env: TestEnvironment, user
):
    controller_service = await request_di_container.get(ControllerService)
    db_session = await request_di_container.get(AsyncSession)

    await controller_service.setup_tasmota(
        SetupTasmotaRequest(controller_id=test_env.controller_1.id, tasmota_id="test")
    )
    await db_session.refresh(test_env.controller_1)
    assert test_env.controller_1.tasmota_id == "test"

    with pytest.raises(TasmotaIDAlreadyTakenError):
        await controller_service.setup_tasmota(
            SetupTasmotaRequest(
                controller_id=test_env.controller_2.id, tasmota_id="test"
            )
        )


@pytest.mark.parametrize("user", ("superadmin",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_read_energy_stats(
    request_di_container: AsyncContainer, test_env: TestEnvironment, user
):
    controller_service = await request_di_container.get(ControllerService)
    db_session = await request_di_container.get(AsyncSession)
    now = datetime.now(UTC)

    for i in ((now - timedelta(days=3)).date(), (now - timedelta(days=1)).date()):
        state = DailyEnergyState(
            controller_id=test_env.controller_1.id,
            energy=100,
            date=i,
        )
        db_session.add(state)
    await db_session.commit()

    response = await controller_service.read_energy_stats(
        GetEnergyStatsRequest(
            controller_id=test_env.controller_1.id,
            period=3,
        )
    )
    assert response.total_energy == 200

    response = await controller_service.read_energy_stats(
        GetEnergyStatsRequest(
            controller_id=test_env.controller_1.id,
            period=1,
        )
    )
    assert response.total_energy == 100

    with pytest.raises(ControllerNotFoundError):
        await controller_service.read_energy_stats(
            GetEnergyStatsRequest(
                controller_id=uuid4(),
                period=1,
            )
        )
