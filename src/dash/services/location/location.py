from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.models.location import Location
from dash.models.user import UserRole
from dash.services.common.errors.base import AccessDeniedError
from dash.services.common.errors.user import UserNotFoundError
from dash.services.location.dto import (
    CreateLocationRequest,
    CreateLocationResponse,
    LocationScheme,
    ReadLocationListResponse,
)
from dash.services.user.user import UserService


class LocationService:
    def __init__(
        self,
        location_repository: LocationRepository,
        controller_repository: ControllerRepository,
        user_repository: UserRepository,
        identity_provider: IdProvider,
        user_service: UserService,
    ) -> None:
        self.location_repository = location_repository
        self.controller_repository = controller_repository
        self.user_repository = user_repository
        self.identity_provider = identity_provider
        self.user_service = user_service

    async def create_location(
        self, data: CreateLocationRequest
    ) -> CreateLocationResponse:
        await self.identity_provider.ensure_superadmin()

        new_user = None
        owner_id = data.owner_id

        if owner_id is not None:
            if not await self.user_repository.exists_by_id(owner_id):
                raise UserNotFoundError
        if data.user is not None:
            new_user = await self.user_service.create_location_owner(data.user)
            owner_id = new_user.id

        location = Location(
            owner_id=owner_id,
            name=data.name,
            address=data.address,
        )
        self.location_repository.add(location)

        await self.location_repository.commit()
        return CreateLocationResponse(location_id=location.id, user=new_user)

    async def read_locations(self) -> ReadLocationListResponse:
        user = await self.identity_provider.get_current_user()

        if user.role is UserRole.SUPERADMIN:
            locations = await self.location_repository.get_list()
        elif user.role is UserRole.LOCATION_OWNER:
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
