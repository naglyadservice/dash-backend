from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from dishka import AsyncContainer

from dash.infrastructure.storages.iot import IoTStorage
from dash.models.admin_user import AdminUser
from dash.services.common.dto import ControllerID
from dash.services.iot.carwash.service import CarwashService
from dash.services.iot.fiscalizer.service import FiscalizerService
from dash.services.iot.wsm.service import WsmService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class IoTDependencies:
    wsm_service: WsmService
    carwash_service: CarwashService
    fiscalizer_service: FiscalizerService
    iot_storage: IoTStorage


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return IoTDependencies(
        wsm_service=await request_di_container.get(WsmService),
        carwash_service=await request_di_container.get(CarwashService),
        fiscalizer_service=await request_di_container.get(FiscalizerService),
        iot_storage=await request_di_container.get(IoTStorage),
    )


@pytest.mark.parametrize("user", ("superadmin",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_read_iot_controller(
    deps: IoTDependencies,
    test_env: TestEnvironment,
    user: AdminUser,
    mocker: Mock,
):
    mocker.patch.object(deps.iot_storage, "is_online", return_value=True)

    response = await deps.wsm_service.read_controller(
        ControllerID(controller_id=test_env.controller_1.id)
    )
    assert response is not None

    response = await deps.carwash_service.read_controller(
        ControllerID(controller_id=test_env.controller_2.id)
    )
    assert response is not None

    response = await deps.fiscalizer_service.read_controller(
        ControllerID(controller_id=test_env.controller_3.id)
    )
    assert response is not None
