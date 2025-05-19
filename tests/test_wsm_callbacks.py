import asyncio
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.infrastructure.iot.wsm import WsmClient
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.storages.iot import IotStorage
from dash.presentation.callbacks_wsm.denomination import (
    DenominationCallbackPayload,
    denomination_callback_retort,
)
from dash.presentation.callbacks_wsm.encashment import (
    EncashmentCallbackPayload,
    encashment_callback_retort,
)
from dash.presentation.callbacks_wsm.sale import (
    SaleCallbackPayload,
    sale_callabck_retort,
)
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class CallbackDependencies:
    iot_storage: IotStorage
    wsm_client: WsmClient


@pytest.fixture
async def deps(request_di_container: AsyncContainer) -> CallbackDependencies:
    return CallbackDependencies(
        iot_storage=await request_di_container.get(IotStorage),
        wsm_client=await request_di_container.get(WsmClient),
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
        di_container=di_container,
    )
    deps.wsm_client.payment_card_ack.assert_called_once_with(
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
    payload = EncashmentCallbackPayload(
        id=1,
        created=datetime(2000, 1, 1),
        coin_1=1,
        coin_2=2,
        coin_3=3,
        coin_4=4,
        coin_5=5,
        coin_6=6,
        bill_1=1,
        bill_2=2,
        bill_3=3,
        bill_4=4,
        bill_5=5,
        bill_6=6,
        bill_7=7,
        bill_8=8,
        amount=100,
    )
    mocker.patch.object(deps.wsm_client, "encashment_ack")

    await deps.wsm_client.dispatcher.encashment._process_callbacks(  # type: ignore
        device_id=str(test_env.controller_1.device_id),
        decoded_payload=encashment_callback_retort.dump(payload),
        di_container=di_container,
    )
    deps.wsm_client.encashment_ack.assert_called_once_with(
        device_id=str(test_env.controller_1.device_id),
        payload={"request_id": 1, "code": 0},
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_payment_card_balance_out(
    di_container: AsyncContainer,
    request_di_container: AsyncContainer,
    test_env: TestEnvironment,
    mocker: Mock,
):
    session = await request_di_container.get(AsyncSession)

    card_balance_out = Decimal(90)
    wsm_client = await di_container.get(WsmClient)
    payload = SaleCallbackPayload(
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
        card_balance_in=10000,
        card_balance_out=int(card_balance_out * 100),
    )
    mocker.patch.object(wsm_client, "sale_ack")

    await wsm_client.dispatcher.sale._process_callbacks(  # type: ignore
        device_id="test_device_id_1",
        decoded_payload=sale_callabck_retort.dump(payload),
        di_container=di_container,
    )
    wsm_client.sale_ack.assert_called_once_with("test_device_id_1", 1)

    await session.refresh(test_env.customer_1)
    assert test_env.customer_1.balance == card_balance_out


@pytest.mark.asyncio(loop_scope="session")
async def test_denomination_callback(
    deps: CallbackDependencies,
    test_env: TestEnvironment,
    mocker: Mock,
    request_di_container: AsyncContainer,
):
    payload = DenominationCallbackPayload(
        created=datetime(2000, 1, 1),
        coin=0,
        bill=2,
    )
    payment_repository = await request_di_container.get(PaymentRepository)
    mocker.patch.object(payment_repository, "add")
    mocker.patch.object(payment_repository, "commit")

    await deps.wsm_client.dispatcher.denomination._process_callbacks(  # type: ignore
        device_id=test_env.controller_1.device_id,
        decoded_payload=denomination_callback_retort.dump(payload),
        di_container=request_di_container,
    )
    payment_repository.add.assert_called_once()
    payment_repository.commit.assert_called_once()
