import asyncio
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.infrastructure.iot.carwash.client import CarwashIoTClient
from dash.infrastructure.iot.fiscalizer.client import FiscalizerIoTClient
from dash.infrastructure.iot.mqtt.client import MqttClient
from dash.infrastructure.iot.wsm.client import WsmIoTClient
from dash.infrastructure.storages.iot import IoTStorage
from dash.presentation.iot_callbacks.carwash.sale import (
    CarwashSaleCallbackPayload,
    carwash_sale_callback_retort,
)
from dash.presentation.iot_callbacks.common.di_injector import default_retort
from dash.presentation.iot_callbacks.fiscalizer.sale import (
    FiscalizerSaleCallbackPayload,
    fiscalizer_sale_callback_retort,
)
from dash.presentation.iot_callbacks.mqtt.tasmota import tasmota_callback_retort
from dash.presentation.iot_callbacks.wsm.encashment import (
    WsmEncashmentCallbackPayload,
    wsm_encashment_callback_retort,
)
from dash.presentation.iot_callbacks.wsm.sale import (
    WsmSaleCallbackPayload,
    wsm_sale_callback_retort,
)
from dash.services.iot.dto import EnergyStateDTO
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class CallbackDependencies:
    iot_storage: IoTStorage
    wsm_client: WsmIoTClient
    fiscalizer_client: FiscalizerIoTClient
    carwash_client: CarwashIoTClient
    mqtt_client: MqttClient


@pytest.fixture
async def deps(request_di_container: AsyncContainer) -> CallbackDependencies:
    return CallbackDependencies(
        iot_storage=await request_di_container.get(IoTStorage),
        wsm_client=await request_di_container.get(WsmIoTClient),
        fiscalizer_client=await request_di_container.get(FiscalizerIoTClient),
        carwash_client=await request_di_container.get(CarwashIoTClient),
        mqtt_client=await request_di_container.get(MqttClient),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_payment_card_get_callback(
    deps: CallbackDependencies,
    test_env: TestEnvironment,
    mocker: Mock,
    di_container: AsyncContainer,
):
    mocker.patch.object(deps.wsm_client, "payment_card_ack")

    await deps.wsm_client.dispatcher.payment_card_get._process_callbacks(  # type: ignore
        device_id=str(test_env.controller_1.device_id),
        decoded_payload={
            "request_id": 1,
            "created": "2000-01-01T12:00:00",
            "cardUID": test_env.customer_1.card_id,
        },
        di_container=di_container,  # type: ignore
    )
    deps.wsm_client.payment_card_ack.assert_called_once_with(  # type: ignore
        device_id=str(test_env.controller_1.device_id),
        payload={
            "request_id": 1,
            "cardUID": test_env.customer_1.card_id,
            "balance": int(test_env.customer_1.balance * 100),
            "tariffPerLiter_1": test_env.customer_1.tariff_per_liter_1,
            "tariffPerLiter_2": test_env.customer_1.tariff_per_liter_2,
            "code": 0,
        },
    )


@pytest.mark.parametrize("user", ("location_admin_1",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_state_info_callback(
    deps: CallbackDependencies,
    test_env: TestEnvironment,
    di_container: AsyncContainer,
    user,
):
    state = {
        "created": "2000-01-01T12:00:00",
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

    state = await deps.iot_storage.get_state(test_env.controller_1.id)
    assert state == state


@pytest.mark.parametrize("user", ("location_admin_1",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_encashment_callback(
    deps: CallbackDependencies,
    test_env: TestEnvironment,
    di_container: AsyncContainer,
    user,
    mocker,
):
    payload = WsmEncashmentCallbackPayload(
        id=1,
        created=datetime(2000, 1, 1),
        coin=[1, 2, 3, 4, 5, 6],
        bill=[1, 2, 3, 4, 5, 6, 7, 8],
        amount=100,
    )
    mocker.patch.object(deps.wsm_client, "encashment_ack")

    await deps.wsm_client.dispatcher.encashment._process_callbacks(
        device_id=str(test_env.controller_1.device_id),
        decoded_payload=wsm_encashment_callback_retort.dump(payload),
        di_container=di_container,  # type: ignore
    )
    deps.wsm_client.encashment_ack.assert_called_once_with(  # type: ignore
        device_id=str(test_env.controller_1.device_id),
        payload={"id": 1, "code": 0},
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_wsm_sale_callback_with_card_balance_out(
    deps: CallbackDependencies,
    request_di_container: AsyncContainer,
    test_env: TestEnvironment,
    mocker: Mock,
):
    session = await request_di_container.get(AsyncSession)
    card_balance_out = Decimal(90)

    payload = WsmSaleCallbackPayload(
        id=1,
        created=datetime(2022, 1, 1),
        add_coin=1,
        add_bill=2,
        add_prev=3,
        add_free=4,
        add_qr=5,
        add_pp=6,
        out_liters_1=7,
        out_liters_2=8,
        sale_type="card",
        card_uid=test_env.customer_1.card_id,
        card_balance_in=int(test_env.customer_1.balance * 100),
        card_balance_out=int(card_balance_out * 100),
    )
    mocker.patch.object(deps.wsm_client, "sale_ack")

    await deps.wsm_client.dispatcher.sale._process_callbacks(  # type: ignore
        device_id=test_env.controller_1.device_id,
        decoded_payload=wsm_sale_callback_retort.dump(payload),
        di_container=request_di_container,  # type: ignore
    )
    deps.wsm_client.sale_ack.assert_called_once_with(  # type: ignore
        test_env.controller_1.device_id, payload.id
    )

    await session.refresh(test_env.customer_1)
    assert test_env.customer_1.balance == card_balance_out


@pytest.mark.asyncio(loop_scope="session")
async def test_carwash_sale_callback_with_card_balance_out(
    deps: CallbackDependencies,
    test_env: TestEnvironment,
    mocker: Mock,
    request_di_container: AsyncContainer,
):
    session = await request_di_container.get(AsyncSession)
    card_balance_out = Decimal(50)

    payload = CarwashSaleCallbackPayload(
        id=1,
        created=datetime(2022, 1, 1),
        add_coin=1,
        add_bill=2,
        add_prev=3,
        add_free=4,
        add_qr=5,
        add_pp=6,
        tariff=[50, 0, 0, 0, 0, 0, 0, 0],
        services_sold=[60, 0, 0, 0, 0, 0, 0, 0],
        sale_type="card",
        card_uid=test_env.customer_2.card_id,
        card_balance_in=int(test_env.customer_2.balance * 100),
        card_balance_out=int(card_balance_out * 100),
    )
    mocker.patch.object(deps.carwash_client, "sale_ack")

    await deps.carwash_client.dispatcher.sale._process_callbacks(  # type: ignore
        device_id=test_env.controller_2.device_id,
        decoded_payload=carwash_sale_callback_retort.dump(payload),
        di_container=request_di_container,  # type: ignore
    )
    deps.carwash_client.sale_ack.assert_called_once_with(  # type: ignore
        test_env.controller_2.device_id, payload.id
    )

    await session.refresh(test_env.customer_2)
    assert test_env.customer_2.balance == 50


@pytest.mark.asyncio(loop_scope="session")
async def test_sys_callbacks(
    deps: CallbackDependencies,
    test_env: TestEnvironment,
    di_container: AsyncContainer,
):
    device_id = str(test_env.controller_1.device_id)
    await deps.mqtt_client.dispatcher.sys_connect._process_callbacks(  # type: ignore
        device_id=device_id,
        decoded_payload={
            "username": device_id,
        },
        di_container=di_container,  # type: ignore
    )

    state = await deps.iot_storage.is_online(device_id)
    assert state is True

    await deps.mqtt_client.dispatcher.sys_disconnect._process_callbacks(  # type: ignore
        device_id=device_id,
        decoded_payload={
            "username": device_id,
        },
        di_container=di_container,  # type: ignore
    )

    state = await deps.iot_storage.is_online(device_id)
    assert state is False


@pytest.mark.asyncio(loop_scope="session")
async def test_tasmota_callback(
    deps: CallbackDependencies,
    test_env: TestEnvironment,
    di_container: AsyncContainer,
):
    payload = {
        "Time": "2024-01-01T12:00:00",
        "ENERGY": {
            "Today": 1.5,
            "Yesterday": 2.5,
            "Total": 100.0,
            "TotalStartTime": "2024-01-01T00:00:00",
            "Power": 100.0,
            "ApparentPower": 120.0,
            "ReactivePower": 60.0,
            "Factor": 0.8,
            "Voltage": 220.0,
            "Current": 0.5,
        },
    }

    await deps.mqtt_client.dispatcher.tasmota_state._process_callbacks(
        device_id=test_env.controller_1.tasmota_id,  # type: ignore
        decoded_payload=payload,
        di_container=di_container,  # type: ignore
    )
    state = await deps.iot_storage.get_energy_state(test_env.controller_1.id)
    assert state == default_retort.dump(
        tasmota_callback_retort.load(payload, EnergyStateDTO)
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_fiscalizer_sale_callback(
    deps: CallbackDependencies,
    request_di_container: AsyncContainer,
    test_env: TestEnvironment,
    mocker: Mock,
):
    payload = FiscalizerSaleCallbackPayload(
        id=1,
        created=datetime(2022, 1, 1),
        add_coin=1,
        add_bill=2,
        add_free=4,
        add_qr=5,
    )
    mocker.patch.object(deps.fiscalizer_client, "sale_ack")

    await deps.fiscalizer_client.dispatcher.sale._process_callbacks(  # type: ignore
        device_id=test_env.controller_3.device_id,
        decoded_payload=fiscalizer_sale_callback_retort.dump(payload),
        di_container=request_di_container,  # type: ignore
    )
    deps.fiscalizer_client.sale_ack.assert_called_once_with(  # type: ignore
        test_env.controller_3.device_id, payload.id
    )
