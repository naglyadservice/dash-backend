from dataclasses import dataclass
from datetime import date

import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.infrastructure.repositories.customer import CustomerRepository
from dash.models.admin_user import AdminUser
from dash.services.customer.dto import (
    CreateCustomerRequest,
    EditCustomerDTO,
    EditCustomerRequest,
    ReadCustomerListRequest,
)
from dash.services.customer.service import CustomerService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class CustomerDependencies:
    customer_service: CustomerService
    customer_repository: CustomerRepository
    db_session: AsyncSession


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return CustomerDependencies(
        customer_service=await request_di_container.get(CustomerService),
        customer_repository=await request_di_container.get(CustomerRepository),
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
            email="test@test.com",
            card_id="test",
            balance=100,
            birth_date=date(2000, 1, 1),
            phone_number="1234567890",
            discount_percent=10,
            tariff_per_liter_1=100,
            tariff_per_liter_2=100,
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
            id=test_env.customer_1.id, user=EditCustomerDTO(name="changed_name")
        )
    )
    await deps.db_session.refresh(test_env.customer_1)
    assert test_env.customer_1.name == "changed_name"
