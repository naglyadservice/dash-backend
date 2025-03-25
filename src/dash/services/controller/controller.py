from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.models.controllers.carwash import CarwashController
from dash.models.controllers.controller import ControllerType
from dash.models.controllers.vacuum import VacuumController
from dash.models.controllers.water_vending import WaterVendingController
from dash.services.controller.dto import (
    AddControllerRequest,
    AddControllerResponse,
    ControllerScheme,
    ReadControllerRequest,
    ReadControllerResponse,
)


class ControllerService:
    def __init__(
        self, identity_provider: IdProvider, controller_repository: ControllerRepository
    ):
        self.identity_provider = identity_provider
        self.controller_repository = controller_repository

    async def read_controllers(
        self, data: ReadControllerRequest
    ) -> ReadControllerResponse:
        await self.identity_provider.ensure_admin()

        controllers, total = await self.controller_repository.get_list(data)

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
