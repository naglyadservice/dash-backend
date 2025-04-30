from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.models.controllers.carwash import CarwashController
from dash.models.controllers.controller import ControllerType
from dash.models.controllers.vacuum import VacuumController
from dash.models.controllers.water_vending import WaterVendingController
from dash.models.user import UserRole
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.common.errors.location import LocationNotFoundError
from dash.services.controller.dto import (
    AddControllerLocationRequest,
    AddControllerRequest,
    AddControllerResponse,
    AddLiqpayCredentialsRequest,
    AddMonopayCredentialsRequest,
    ControllerScheme,
    ReadControllerListRequest,
    ReadControllerResponse,
)


class ControllerService:
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        location_repository: LocationRepository,
    ):
        self.identity_provider = identity_provider
        self.controller_repository = controller_repository
        self.location_repository = location_repository

    async def read_controllers(
        self, data: ReadControllerListRequest
    ) -> ReadControllerResponse:
        user = await self.identity_provider.get_current_user()

        if data.location_id:
            await self.identity_provider.ensure_location_admin(data.location_id)

        if user.role is UserRole.SUPERADMIN:
            controllers, total = await self.controller_repository.get_list_all(data)
        elif user.role is UserRole.LOCATION_OWNER:
            controllers, total = await self.controller_repository.get_list_by_owner(
                data, user.id
            )
        elif user.role is UserRole.LOCATION_ADMIN:
            controllers, total = await self.controller_repository.get_list_by_admin(
                data, user.id
            )
        else:
            raise AccessForbiddenError

        return ReadControllerResponse(
            controllers=[
                ControllerScheme.model_validate(controller)
                for controller in controllers
            ],
            total=total,
        )

    async def add_controller(self, data: AddControllerRequest) -> AddControllerResponse:
        await self.identity_provider.ensure_superadmin()

        base_controller = data.model_dump()

        if data.type is ControllerType.WATER_VENDING:
            controller = WaterVendingController(**base_controller)

        if data.type is ControllerType.CARWASH:
            controller = CarwashController(**base_controller)

        if data.type is ControllerType.VACUUM:
            controller = VacuumController(**base_controller)

        self.controller_repository.add(controller)
        await self.controller_repository.commit()

        return AddControllerResponse(id=controller.id)

    async def add_monopay_credentials(self, data: AddMonopayCredentialsRequest) -> None:
        controller = await self.controller_repository.get(data.controller_id)
        if not controller:
            raise ControllerNotFoundError

        await self.identity_provider.ensure_location_owner(controller.location_id)

        controller.monopay_token = data.monopay.token
        controller.monopay_active = data.monopay.is_active

        await self.controller_repository.commit()

    async def add_liqpay_credentials(self, data: AddLiqpayCredentialsRequest) -> None:
        controller = await self.controller_repository.get(data.controller_id)
        if not controller:
            raise ControllerNotFoundError

        await self.identity_provider.ensure_location_owner(controller.location_id)

        controller.liqpay_private_key = data.liqpay.private_key
        controller.liqpay_public_key = data.liqpay.public_key
        controller.liqpay_active = data.liqpay.is_active

        await self.controller_repository.commit()

    async def add_location(self, data: AddControllerLocationRequest) -> None:
        await self.identity_provider.ensure_superadmin()

        if not await self.location_repository.exists(data.location_id):
            raise LocationNotFoundError

        controller = await self.controller_repository.get(data.controller_id)
        if not controller:
            raise ControllerNotFoundError

        controller.location_id = data.location_id
        await self.controller_repository.commit()
