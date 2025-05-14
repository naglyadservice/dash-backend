import asyncio
from dataclasses import dataclass

import pytest
from dishka import AsyncContainer

from dash.infrastructure.iot.wsm.client import WsmClient
from dash.infrastructure.storages.iot import IotStorage
from dash.presentation.callbacks_wsm.payment_card_get import payment_card_get_callback
from dash.services.water_vending.water_vending import WaterVendingService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class CallbackDependencies:
    iot_storage: IotStorage
    wsm_client: WsmClient
    wsm_service: WaterVendingService


@pytest.fixture
async def deps(request_di_container: AsyncContainer) -> CallbackDependencies:
    return CallbackDependencies(
        iot_storage=await request_di_container.get(IotStorage),
        wsm_client=await request_di_container.get(WsmClient),
        wsm_service=await request_di_container.get(WaterVendingService),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_payment_card_get_callback(di_container: AsyncContainer):
    # TODO: implement cases
    await payment_card_get_callback(
        "test_device_id",
        {"request_id": 1, "created": "test_created", "cardUID": "test_card_uid"},
        di_container=di_container,  # type: ignore
    )


@pytest.mark.parametrize("user", ("superadmin",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_state_info_callback(
    deps: CallbackDependencies,
    test_env: TestEnvironment,
    di_container: AsyncContainer,
    user,
):
    state = {
        "created": "2025-05-14T20:28:01",
        "summaInBox": 500,
        "litersInTank": 7500,
        "operatingMode": "WAIT",
        "tankLowLevelSensor": True,
        "tankHighLevelSensor": True,
        "depositBoxSensor": False,
        "doorSensor": False,
        "coinState": 0,
        "billState": 0,
        "errors": {
            "lowLevelSensor": False,
            "ServerBlock": False,
            "pour_1": False,
            "pour_2": False,
            "coinValidator": False,
            "billValidator": True,
            "PayPass": False,
            "Card": False,
        },
    }
    await deps.wsm_client.dispatcher.state_info._process_callbacks(
        device_id=str(test_env.controller_1.device_id),
        decoded_payload=state,
        di_container=di_container,  # type: ignore
    )
    await asyncio.sleep(0.1)

    assert await deps.iot_storage.get_state(test_env.controller_1.id) == state
