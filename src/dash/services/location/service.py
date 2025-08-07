from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.company import CompanyRepository
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.models.admin_user import AdminRole
from dash.models.location import Location
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.company import CompanyNotFoundError
from dash.services.common.errors.location import LocationNotFoundError
from dash.services.location.dto import (
    AttachLocationToCompanyRequest,
    CreateLocationRequest,
    CreateLocationResponse,
    EditLocationRequest,
    LocationScheme,
    ReadLocationListRequest,
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

    async def read_locations(
        self, data: ReadLocationListRequest
    ) -> ReadLocationListResponse:
        user = await self.identity_provider.authorize()

        if data.company_id is not None:
            await self.identity_provider.ensure_company_owner(data.company_id)
            locations, total = await self.location_repository.get_list_all(data)

        else:
            match user.role:
                case AdminRole.SUPERADMIN:
                    locations, total = await self.location_repository.get_list_all(data)
                case AdminRole.COMPANY_OWNER:
                    locations, total = await self.location_repository.get_list_by_owner(
                        data, user.id
                    )
                case AdminRole.LOCATION_ADMIN:
                    locations, total = await self.location_repository.get_list_by_admin(
                        data, user.id
                    )
                case _:
                    raise AccessForbiddenError

        return ReadLocationListResponse(
            locations=[
                LocationScheme.model_validate(location, from_attributes=True)
                for location in locations
            ],
            total=total,
        )

    async def edit_location(self, data: EditLocationRequest) -> None:
        await self.identity_provider.ensure_company_owner(location_id=data.location_id)

        location = await self.location_repository.get(data.location_id)
        if not location:
            raise LocationNotFoundError

        dict_data = data.data.model_dump(exclude_unset=True)
        for key, value in dict_data.items():
            if hasattr(location, key):
                setattr(location, key, value)

        await self.location_repository.commit()

    async def attach_location_to_company(
        self, data: AttachLocationToCompanyRequest
    ) -> None:
        await self.identity_provider.ensure_superadmin()

        if not await self.company_repository.exists(data.company_id):
            raise CompanyNotFoundError

        location = await self.location_repository.get(data.location_id)
        if not location:
            raise LocationNotFoundError

        location.company_id = data.company_id
        await self.location_repository.commit()
