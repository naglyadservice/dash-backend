from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.infrastructure.acquiring.monopay import MonopayGateway
from dash.infrastructure.iot.laundry.client import LaundryIoTClient
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.repositories.transaction import (
    LaundryTransaction,
    TransactionRepository,
)
from dash.models.controllers.laundry import LaundryTariffType
from dash.models.payment import Payment, PaymentStatus, PaymentType, PaymentGatewayType
from dash.models.transactions.laundry import LaundrySessionStatus
from dash.services.iot.dto import CreateInvoiceResponse
from dash.services.iot.laundry.dto import CreateLaundryInvoiceRequest
from dash.services.iot.laundry.service import LaundryService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class LaundryDependencies:
    service: LaundryService
    liqpay: MonopayGateway
    monopay: MonopayGateway
    payment_repo: PaymentRepository
    transaction_repo: TransactionRepository
    iot: LaundryIoTClient
    session: AsyncSession


@pytest.fixture
async def deps(request_di_container: AsyncContainer) -> LaundryDependencies:
    return LaundryDependencies(
        service=await request_di_container.get(LaundryService),
        liqpay=await request_di_container.get(MonopayGateway),
        monopay=await request_di_container.get(MonopayGateway),
        payment_repo=await request_di_container.get(PaymentRepository),
        transaction_repo=await request_di_container.get(TransactionRepository),
        iot=await request_di_container.get(LaundryIoTClient),
        session=await request_di_container.get(AsyncSession),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_session_fixed(
    deps: LaundryDependencies,
    test_env: TestEnvironment,
    mocker: Mock,
    request_di_container: AsyncContainer,
):
    mocker.patch.object(
        deps.liqpay,
        "create_invoice",
        return_value=CreateInvoiceResponse(
            invoice_url="some.url", invoice_id=str(uuid4())
        ),
    )
    mocker.patch.object(deps.iot, "unlock_button_and_turn_on_led")
    mocker.patch.object(deps.iot, "lock_button_and_turn_off_led")
    mocker.patch.object(deps.service, "healthcheck")

    result = await deps.service.create_invoice(
        CreateLaundryInvoiceRequest(
            controller_id=test_env.laundry_controller_fixed.id,
            gateway_type=PaymentGatewayType.LIQPAY,
            redirect_url="test",
        )
    )
    payment = await deps.payment_repo.get_by_invoice_id(result.invoice_id)
    assert payment is not None

    await deps.service.process_hold_status(payment)
    deps.iot.unlock_button_and_turn_on_led.assert_called_once()  # type: ignore

    transaction = await deps.transaction_repo.get_laundry_active(
        test_env.laundry_controller_fixed.id
    )
    assert transaction is not None
    assert transaction.session_status is LaundrySessionStatus.WAITING_START

    # Ensure the same state doesn't trigger event twice
    for _ in range(2):
        await deps.iot.dispatcher.state_info._process_callbacks(
            device_id=test_env.laundry_controller_fixed.device_id,
            decoded_payload={"input": [{"id": 1, "state": True}]},
            di_container=request_di_container,  # type: ignore
        )

    assert deps.iot.lock_button_and_turn_off_led.call_count == 1  # type: ignore
    await deps.session.refresh(transaction)
    assert transaction.session_status is LaundrySessionStatus.IN_PROGRESS

    for _ in range(2):
        await deps.iot.dispatcher.state_info._process_callbacks(
            device_id=test_env.laundry_controller_fixed.device_id,
            decoded_payload={"input": [{"id": 1, "state": False}]},
            di_container=request_di_container,  # type: ignore
        )

    await deps.session.refresh(transaction)
    assert transaction.session_status is LaundrySessionStatus.COMPLETED
    assert transaction.final_amount == test_env.laundry_controller_fixed.fixed_price


@pytest.mark.asyncio(loop_scope="session")
async def test_per_minute_tariff(
    deps: LaundryDependencies,
    test_env: TestEnvironment,
):
    controller = test_env.laundry_controller_per_minute

    payment = Payment(
        id=uuid4(),
        amount=controller.max_hold_amount,
        status=PaymentStatus.COMPLETED,
        type=PaymentType.CASHLESS,
        gateway_type=PaymentGatewayType.MONOPAY,
    )
    transaction = LaundryTransaction(
        payment_id=payment.id,
        tariff_type=LaundryTariffType.PER_MINUTE,
        session_status=LaundrySessionStatus.IN_PROGRESS,
        session_start_time=datetime.now(UTC) - timedelta(minutes=40),
        hold_amount=controller.max_hold_amount,
        final_amount=0,
        refund_amount=0,
        payment=payment,
    )
    deps.service._calculate_per_minute_tariff(transaction, controller)
    assert transaction.final_amount == 7000

    transaction.session_start_time = datetime.now(UTC) - timedelta(minutes=30)
    deps.service._calculate_per_minute_tariff(transaction, controller)
    assert transaction.final_amount == 6000

    transaction.session_start_time = datetime.now(UTC) - timedelta(minutes=1000)
    deps.service._calculate_per_minute_tariff(transaction, controller)
    assert transaction.final_amount == controller.max_hold_amount
