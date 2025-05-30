from dataclasses import dataclass

import pytest
from dishka import AsyncContainer

from dash.models.admin_user import AdminUser
from dash.services.common.dto import ControllerID
from dash.services.iot.carwash.service import CarwashService
from dash.services.iot.wsm.service import WsmService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class IotDependencies:
    wsm_service: WsmService
    carwash_service: CarwashService


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return IotDependencies(
        wsm_service=await request_di_container.get(WsmService),
        carwash_service=await request_di_container.get(CarwashService),
    )


@pytest.mark.parametrize("user", ("superadmin",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_read_iot_controller(
    deps: IotDependencies,
    test_env: TestEnvironment,
    user: AdminUser,
):
    response = await deps.wsm_service.read_controller(
        ControllerID(controller_id=test_env.controller_1.id)
    )
    assert response is not None

    response = await deps.carwash_service.read_controller(
        ControllerID(controller_id=test_env.controller_2.id)
    )
    assert response is not None
