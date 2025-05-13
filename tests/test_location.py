from dataclasses import dataclass

import pytest
from dishka import AsyncContainer

from dash.infrastructure.repositories.location import LocationRepository
from dash.models.admin_user import AdminUser
from dash.services.common.errors.base import AccessDeniedError, AccessForbiddenError
from dash.services.location.dto import CreateLocationRequest, ReadLocationListRequest
from dash.services.location.location import LocationService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class LocationDependencies:
    location_service: LocationService
    location_repository: LocationRepository


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return LocationDependencies(
        location_service=await request_di_container.get(LocationService),
        location_repository=await request_di_container.get(LocationRepository),
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
async def test_create_location(
    deps: LocationDependencies,
    user: AdminUser,
    error: Exception,
    test_env: TestEnvironment,
):
    try:
        response = await deps.location_service.create_location(
            CreateLocationRequest(
                name="test",
                address="test",
                company_id=test_env.company_1.id,
            )
        )
    except Exception as e:
        assert error == e
    else:
        location = await deps.location_repository.get(response.location_id)
        assert (
            location is not None
            and location.name == "test"
            and location.company_id is not None
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
async def test_read_locations(deps: LocationDependencies, user: AdminUser, result: int):
    response = await deps.location_service.read_locations(ReadLocationListRequest())
    assert response.total == result


@pytest.mark.parametrize(
    "user, error, result",
    [
        ("company_owner_1", None, 1),
        ("location_admin_1", AccessDeniedError(), 1),
    ],
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_read_locations_by_company_id(
    deps: LocationDependencies,
    user: AdminUser,
    test_env: TestEnvironment,
    error: Exception,
    result: int,
):
    try:
        response = await deps.location_service.read_locations(
            ReadLocationListRequest(company_id=test_env.company_1.id)
        )
    except Exception as e:
        assert error == e
    else:
        assert response.total == result
