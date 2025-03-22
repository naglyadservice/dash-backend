from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.services.controller.dto import (
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
        controllers, total = await self.controller_repository.get_list(data)

        return ReadControllerResponse(
            controllers=[
                ControllerScheme.model_validate(controller)
                for controller in controllers
            ],
            total=total,
        )
