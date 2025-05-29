import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.services.common.errors.controller import TasmotaIDAlreadyTakenError
from dash.services.controller.dto import SetupTasmotaRequest
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
