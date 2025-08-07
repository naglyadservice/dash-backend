from dataclasses import dataclass

import pytest
from dishka import AsyncContainer

from dash.infrastructure.repositories.company import CompanyRepository
from dash.models.admin_user import AdminUser
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.company.dto import CreateCompanyRequest
from dash.services.company.service import CompanyService
from dash.services.user.dto import CreateUserRequest
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class CompanyDependencies:
    company_service: CompanyService
    company_repository: CompanyRepository


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return CompanyDependencies(
        company_service=await request_di_container.get(CompanyService),
        company_repository=await request_di_container.get(CompanyRepository),
    )


@pytest.mark.parametrize(
    "user, error",
    [
        ("superadmin", None),
        ("company_owner_1", AccessForbiddenError()),
        ("location_admin_1", AccessForbiddenError()),
    ],
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_create_company_with_new_owner(
    deps: CompanyDependencies, user: AdminUser, error: Exception
):
    try:
        response = await deps.company_service.create_company(
            CreateCompanyRequest(
                name="test",
                new_owner=CreateUserRequest(email="test@test.com", name="Test User"),
            )
        )
    except Exception as e:
        assert error == e
    else:
        company = await deps.company_repository.get(response.company_id)
        assert (
            company is not None and company.name == "test" and company.owner is not None
        )


@pytest.mark.parametrize(
    "user, error",
    [
        ("superadmin", None),
        ("company_owner_1", AccessForbiddenError()),
        ("location_admin_1", AccessForbiddenError()),
    ],
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_create_company_with_existing_owner(
    deps: CompanyDependencies,
    user: AdminUser,
    error: Exception,
    test_env: TestEnvironment,
):
    try:
        response = await deps.company_service.create_company(
            CreateCompanyRequest(name="test", owner_id=test_env.company_owner_1.id)
        )
    except Exception as e:
        assert error == e
    else:
        company = await deps.company_repository.get(response.company_id)
        assert (
            company is not None and company.name == "test" and company.owner is not None
        )


@pytest.mark.parametrize(
    "user, result, error",
    [
        ("superadmin", 2, None),
        ("company_owner_1", 1, None),
        ("company_owner_2", 1, None),
        ("location_admin_1", None, AccessForbiddenError()),
    ],
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_read_companies(
    deps: CompanyDependencies, user: AdminUser, result: int, error: Exception
):
    try:
        response = await deps.company_service.read_companies()
    except Exception as e:
        assert error == e
    else:
        assert len(response.companies) == result
