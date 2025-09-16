import uuid
from dataclasses import dataclass
from datetime import date

import pytest
from aiohttp.test_utils import make_mocked_coro
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.infrastructure.auth.auth_service import AuthService
from dash.infrastructure.auth.dto import (
    CompleteCustomerRegistrationRequest,
    CompletePasswordResetRequest,
    LoginCustomerRequest,
    RegisterCustomerRequest,
    StartPasswordResetRequest,
)
from dash.infrastructure.auth.sms_sender import SMSClient
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.models.admin_user import AdminUser
from dash.services.common.errors.company import CompanyNotFoundError
from dash.services.common.errors.user import (
    CustomerNotFoundError,
    PhoneNumberAlreadyTakenError,
)
from dash.services.customer.dto import (
    ChangeCustomerPasswordRequest,
    CreateCustomerRequest,
    EditCustomerDTO,
    EditCustomerRequest,
    ReadCustomerListRequest,
    UpdateCustomerProfileRequest,
)
from dash.services.customer.service import CustomerService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class CustomerDependencies:
    customer_service: CustomerService
    customer_repository: CustomerRepository
    auth: AuthService
    sms_client: SMSClient
    db_session: AsyncSession


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return CustomerDependencies(
        customer_service=await request_di_container.get(CustomerService),
        customer_repository=await request_di_container.get(CustomerRepository),
        auth=await request_di_container.get(AuthService),
        sms_client=await request_di_container.get(SMSClient),
        db_session=await request_di_container.get(AsyncSession),
    )


@pytest.mark.parametrize(
    "user",
    ("superadmin", "company_owner_1", "location_admin_1"),
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_create_customer(
    deps: CustomerDependencies, user: AdminUser, test_env: TestEnvironment
):
    response = await deps.customer_service.create_customer(
        CreateCustomerRequest(
            company_id=test_env.company_1.id,
            name="test",
            card_id="test",
            balance=100,
            birth_date=date(2000, 1, 1),
            phone_number="1234567890",
            discount_percent=10,
            tariff_per_liter_1=100,
            tariff_per_liter_2=100,
            readable_card_code=None,
        )
    )
    assert await deps.customer_repository.exists_by_id(
        test_env.company_1.id, response.id
    )


@pytest.mark.parametrize(
    "user, result",
    [
        ("superadmin", 2),
        ("company_owner_1", 1),
        ("company_owner_2", 1),
        ("location_admin_1", 1),
        ("location_admin_2", 1),
    ],
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_read_customers(deps: CustomerDependencies, user: AdminUser, result: int):
    response = await deps.customer_service.read_customers(ReadCustomerListRequest())
    assert response.total == result


@pytest.mark.parametrize(
    "user",
    ("superadmin", "company_owner_1", "location_admin_1"),
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_edit_customer(
    deps: CustomerDependencies, user: AdminUser, test_env: TestEnvironment
):
    await deps.customer_service.edit_customer(
        EditCustomerRequest(
            id=test_env.customer_1.id, user=EditCustomerDTO(balance=1000)
        )
    )
    await deps.db_session.refresh(test_env.customer_1)
    assert test_env.customer_1.balance == 1000


@pytest.mark.asyncio(loop_scope="session")
async def test_customer_registration(
    deps: CustomerDependencies, test_env: TestEnvironment, mocker
):
    mocker.patch.object(deps.auth, "_generate_code", return_value="1111")

    mocker.patch.object(
        deps.auth.sms_client,
        "send_sms",
        new_callable=make_mocked_coro,
    )

    dto = RegisterCustomerRequest(
        name="test",
        phone_number="test",
        password="test",
        company_id=test_env.company_1.id,
    )

    await deps.auth.start_customer_registration(dto)
    deps.auth.sms_client.send_sms.assert_called_once()  # type: ignore

    await deps.auth.complete_customer_registration(
        CompleteCustomerRegistrationRequest(code="1111")
    )

    with pytest.raises(PhoneNumberAlreadyTakenError):
        await deps.auth.start_customer_registration(dto)

    with pytest.raises(CompanyNotFoundError):
        dto.company_id = uuid.uuid4()
        await deps.auth.start_customer_registration(dto)


@pytest.mark.asyncio(loop_scope="session")
async def test_customer_password_reset(
    deps: CustomerDependencies, test_env: TestEnvironment, mocker
):
    mocker.patch.object(deps.auth, "_generate_code", return_value="1111")
    mocker.patch.object(deps.auth.sms_client, "send_sms", new_callable=make_mocked_coro)

    await deps.auth.start_password_reset(
        StartPasswordResetRequest(
            phone_number=test_env.customer_1.phone_number,
            company_id=test_env.company_1.id,
        )
    )

    await deps.auth.complete_password_reset(
        CompletePasswordResetRequest(
            code="1111",
            new_password="newpwd",
        )
    )

    resp = await deps.auth.authenticate_customer(
        LoginCustomerRequest(
            phone_number=test_env.customer_1.phone_number,
            password="newpwd",
            company_id=test_env.company_1.id,
        )
    )
    assert resp.access_token and resp.refresh_token

    with pytest.raises(CustomerNotFoundError):
        await deps.auth.start_password_reset(
            StartPasswordResetRequest(
                phone_number="wrong",
                company_id=test_env.company_1.id,
            )
        )


@pytest.mark.parametrize("user", ("customer_1",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_change_passsword(deps: CustomerDependencies, user):
    await deps.customer_service.change_password(
        ChangeCustomerPasswordRequest(
            current_password="test",
            new_password="newpwd",
        )
    )
    resp = await deps.auth.authenticate_customer(
        LoginCustomerRequest(
            phone_number=user.phone_number,
            password="newpwd",
            company_id=user.company_id,
        )
    )
    assert resp.access_token and resp.refresh_token


@pytest.mark.parametrize("user", ("customer_1",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_read_me(deps: CustomerDependencies, user):
    resp = await deps.customer_service.read_profile()
    assert resp.name == user.name


@pytest.mark.parametrize("user", ("customer_1",), indirect=["user"])
@pytest.mark.asyncio(loop_scope="session")
async def test_customer_update_profile(deps: CustomerDependencies, user):
    await deps.customer_service.update_profile(
        UpdateCustomerProfileRequest(
            name="new name",
        )
    )
    await deps.db_session.refresh(user)
    assert user.name == "new name"
