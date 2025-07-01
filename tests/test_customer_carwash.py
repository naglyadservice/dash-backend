from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from dishka import AsyncContainer

from dash.infrastructure.auth.token_processor import JWTTokenProcessor
from dash.infrastructure.iot.carwash.client import CarwashIoTClient
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.storages.carwash_session import CarwashSessionStorage
from dash.services.common.errors.customer_carwash import (
    CarwashSessionActiveError,
    CarwashSessionNotFoundError,
)
from dash.services.iot.carwash.customer_dto import (
    FinishCarwashSessionRequest,
    SelectCarwashModeRequest,
    StartCarwashSessionRequest,
)
from dash.services.iot.carwash.customer_service import CustomerCarwashService
from dash.services.iot.carwash.dto import CarwashActionDTO
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class Deps:
    service: CustomerCarwashService
    session_storage: CarwashSessionStorage
    carwash_client: CarwashIoTClient
    customer_repo: CustomerRepository
    token_processor: JWTTokenProcessor


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return Deps(
        service=await request_di_container.get(CustomerCarwashService),
        session_storage=await request_di_container.get(CarwashSessionStorage),
        carwash_client=await request_di_container.get(CarwashIoTClient),
        customer_repo=await request_di_container.get(CustomerRepository),
        token_processor=await request_di_container.get(JWTTokenProcessor),
    )


@pytest.fixture
async def auth_customer(test_env: TestEnvironment, deps: Deps, mocker):
    customer = test_env.customer_1
    mocker.patch.object(
        deps.token_processor,
        "validate_access_token",
        return_value=customer.id,
    )
    return customer


@pytest.mark.asyncio(loop_scope="session")
async def test_start_and_finish_session(
    deps: Deps, test_env: TestEnvironment, auth_customer, mocker
):
    controller_id: UUID = test_env.controller_2.id

    mocker.patch.object(deps.carwash_client, "set_payment")
    mocker.patch.object(deps.carwash_client, "set_action")

    start_req = StartCarwashSessionRequest(controller_id=controller_id, amount=1000)
    old_balance = auth_customer.balance

    await deps.service.start_session(start_req)
    assert await deps.session_storage.is_active(controller_id)
    assert auth_customer.balance == old_balance - Decimal(start_req.amount / 100)
    deps.carwash_client.set_payment.assert_called_once()  # type: ignore

    mode_req = SelectCarwashModeRequest(
        controller_id=controller_id, mode=CarwashActionDTO(Service="Foam")
    )
    await deps.service.select_mode(mode_req)
    deps.carwash_client.set_action.assert_called_once()  # type: ignore

    finish_req = FinishCarwashSessionRequest(controller_id=controller_id)
    await deps.service.finish_session(finish_req)
    assert not await deps.session_storage.is_active(controller_id)


@pytest.mark.asyncio(loop_scope="session")
async def test_start_session_when_active(
    deps: Deps, test_env: TestEnvironment, auth_customer, mocker
):
    controller_id = test_env.controller_1.id
    mocker.patch.object(deps.carwash_client, "set_payment", new_callable=AsyncMock)

    await deps.session_storage.set_session(controller_id, auth_customer.id, 600)

    with pytest.raises(CarwashSessionActiveError):
        await deps.service.start_session(
            StartCarwashSessionRequest(controller_id=controller_id, amount=10)
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_select_mode_without_session(
    deps: Deps, test_env: TestEnvironment, auth_customer
):
    controller_id = test_env.controller_1.id

    with pytest.raises(CarwashSessionNotFoundError):
        await deps.service.select_mode(
            SelectCarwashModeRequest(
                controller_id=controller_id, mode=CarwashActionDTO(Service="Foam")
            )
        )


@pytest.mark.asyncio(loop_scope="session")
async def test_finish_session_without_session(
    deps: Deps, test_env: TestEnvironment, auth_customer
):
    controller_id = test_env.controller_1.id

    with pytest.raises(CarwashSessionNotFoundError):
        await deps.service.finish_session(
            FinishCarwashSessionRequest(controller_id=controller_id)
        )
