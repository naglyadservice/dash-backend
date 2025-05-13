from datetime import datetime
from decimal import Decimal

import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.infrastructure.iot.wsm.client import WsmClient
from dash.presentation.callbacks_wsm.sale import (
    SaleCallbackPayload,
    sale_callabck_retort,
)
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@pytest.mark.asyncio(loop_scope="session")
async def test_payment_card_balance_out(
    di_container: AsyncContainer,
    request_di_container: AsyncContainer,
    test_env: TestEnvironment,
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

    await wsm_client.dispatcher.sale._process_callbacks(  # type: ignore
        device_id="test_device_id_1",
        decoded_payload=sale_callabck_retort.dump(payload),
        di_container=di_container,
    )

    await session.refresh(test_env.customer_1)

    assert test_env.customer_1.balance == card_balance_out
