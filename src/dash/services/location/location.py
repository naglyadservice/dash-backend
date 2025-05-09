from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.company import CompanyRepository
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.models.location import Location
from dash.models.user import UserRole
from dash.services.common.errors.base import AccessDeniedError
from dash.services.common.errors.company import CompanyNotFoundError
from dash.services.location.dto import (
    CreateLocationRequest,
    CreateLocationResponse,
    LocationScheme,
    ReadLocationListResponse,
)


class LocationService:
    def __init__(
        self,
        location_repository: LocationRepository,
        controller_repository: ControllerRepository,
        user_repository: UserRepository,
        identity_provider: IdProvider,
        company_repository: CompanyRepository,
    ) -> None:
        self.location_repository = location_repository
        self.controller_repository = controller_repository
        self.user_repository = user_repository
        self.identity_provider = identity_provider
        self.company_repository = company_repository

    async def create_location(
        self, data: CreateLocationRequest
    ) -> CreateLocationResponse:
        await self.identity_provider.ensure_superadmin()

        if not await self.company_repository.exists(data.company_id):
            raise CompanyNotFoundError

        location = Location(
            company_id=data.company_id,
            name=data.name,
            address=data.address,
        )
        self.location_repository.add(location)
        await self.location_repository.commit()

        return CreateLocationResponse(location_id=location.id)

    async def read_locations(self) -> ReadLocationListResponse:
        user = await self.identity_provider.authorize()

        if user.role is UserRole.SUPERADMIN:
            locations = await self.location_repository.get_list_all()
        elif user.role is UserRole.COMPANY_OWNER:
            locations = await self.location_repository.get_list_by_owner(user.id)
        elif user.role is UserRole.LOCATION_ADMIN:
            locations = await self.location_repository.get_list_by_admin(user.id)
        else:
            raise AccessDeniedError

        return ReadLocationListResponse(
            locations=[
                LocationScheme.model_validate(location, from_attributes=True)
                for location in locations
            ]
        )
