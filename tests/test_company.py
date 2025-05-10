from dataclasses import dataclass

import pytest
from dishka import AsyncContainer

from dash.infrastructure.repositories.company import CompanyRepository
from dash.models.admin_user import AdminUser
from dash.services.company.company import CompanyService
from dash.services.company.dto import CreateCompanyRequest
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


@pytest.mark.asyncio(loop_scope="session")
async def test_create_company_with_new_owner(
    deps: CompanyDependencies, superadmin: AdminUser
):
    response = await deps.company_service.create_company(
        CreateCompanyRequest(
            name="test",
            new_owner=CreateUserRequest(email="test@test.com", name="Test User"),
        )
    )
    company = await deps.company_repository.get(response.company_id)
    assert company is not None and company.name == "test" and company.owner is not None


@pytest.mark.asyncio(loop_scope="session")
async def test_create_company_with_existing_owner(
    deps: CompanyDependencies, test_env: TestEnvironment, superadmin: AdminUser
):
    response = await deps.company_service.create_company(
        CreateCompanyRequest(name="test", owner_id=test_env.company_owner.id)
    )
    company = await deps.company_repository.get(response.company_id)
    assert company is not None and company.name == "test" and company.owner is not None


### We can use test_env users as auth users and test methods that require auth, but i found it's harder to test cuz we need to write more code.
### May be better to test permissions in separate test module? May be you'll find some better way to handle it? ###

# @pytest.mark.asyncio(loop_scope="session")
# async def test_read_companies(deps: CompanyDependencies, company_owner: User):
#     response = await deps.company_service.read_companies()
#     assert len(response.companies) == 1
