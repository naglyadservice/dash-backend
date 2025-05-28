from typing import Sequence
from uuid import UUID

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.encashment import EncashmentRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.models.admin_user import AdminRole, AdminUser
from dash.models.controllers.carwash import CarwashController
from dash.models.controllers.controller import Controller, ControllerType
from dash.models.controllers.vacuum import VacuumController
from dash.models.controllers.water_vending import WaterVendingController
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    TasmotaIDAlreadyTakenError,
)
from dash.services.common.errors.encashment import (
    EncashmentAlreadyClosedError,
    EncashmentNotFoundError,
)
from dash.services.common.errors.location import LocationNotFoundError
from dash.services.controller.dto import (
    AddCheckboxCredentialsRequest,
    AddControllerLocationRequest,
    AddControllerRequest,
    AddControllerResponse,
    AddLiqpayCredentialsRequest,
    AddMonopayCredentialsRequest,
    CloseEncashmentRequest,
    ControllerScheme,
    EditControllerRequest,
    EncashmentScheme,
    PublicCarwashScheme,
    PublicWsmScheme,
    ReadControllerListRequest,
    ReadControllerRequest,
    ReadControllerResponse,
    ReadEncashmentListRequest,
    ReadEncashmentListResponse,
    ReadPublicControllerListRequest,
    ReadPublicControllerListResponse,
    SetupTasmotaRequest,
)
from dash.services.iot.factory import IoTServiceFactory


class ControllerService:
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        location_repository: LocationRepository,
        encashment_repository: EncashmentRepository,
        factory: IoTServiceFactory,
    ):
        self.identity_provider = identity_provider
        self.controller_repository = controller_repository
        self.location_repository = location_repository
        self.encashment_repository = encashment_repository
        self.factory = factory

    async def _get_controller(self, controller_id: UUID) -> Controller:
        controller = await self.controller_repository.get(controller_id)
        if not controller:
            raise ControllerNotFoundError
        return controller

    async def _get_controllers_by_role(
        self, data: ReadControllerListRequest, user: AdminUser
    ) -> tuple[Sequence[Controller], int]:
        match user.role:
            case AdminRole.SUPERADMIN:
                return await self.controller_repository.get_list_all(data)
            case AdminRole.COMPANY_OWNER:
                return await self.controller_repository.get_list_by_owner(data, user.id)
            case AdminRole.LOCATION_ADMIN:
                return await self.controller_repository.get_list_by_admin(data, user.id)
            case _:
                raise AccessForbiddenError

    async def read_controllers(
        self, data: ReadControllerListRequest
    ) -> ReadControllerResponse:
        user = await self.identity_provider.authorize()

        if data.location_id:
            await self.identity_provider.ensure_location_admin(data.location_id)
            controllers, total = await self.controller_repository.get_list_by_admin(
                data, user.id
            )

        elif data.company_id:
            await self.identity_provider.ensure_company_owner(data.company_id)
            controllers, total = await self.controller_repository.get_list_by_owner(
                data, user.id
            )
        else:
            controllers, total = await self._get_controllers_by_role(data, user)

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

        await self.factory.get(controller.type).init_controller_settings(controller)

        self.controller_repository.add(controller)
        await self.controller_repository.commit()

        return AddControllerResponse(id=controller.id)

    async def add_monopay_credentials(self, data: AddMonopayCredentialsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        controller.monopay_token = data.monopay.token
        controller.monopay_active = data.monopay.is_active

        await self.controller_repository.commit()

    async def add_liqpay_credentials(self, data: AddLiqpayCredentialsRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(
            location_id=controller.location_id
        )

        controller.liqpay_private_key = data.liqpay.private_key
        controller.liqpay_public_key = data.liqpay.public_key
        controller.liqpay_active = data.liqpay.is_active

        await self.controller_repository.commit()

    async def add_checkbox_credentials(
        self, data: AddCheckboxCredentialsRequest
    ) -> None:
        controller = await self._get_controller(data.controller_id)

        controller.checkbox_login = data.checkbox.cashier_login
        controller.checkbox_password = data.checkbox.cashier_password
        controller.checkbox_license_key = data.checkbox.license_key
        controller.good_name = data.checkbox.good_name
        controller.good_code = data.checkbox.good_code
        controller.tax_code = data.checkbox.tax_code
        controller.checkbox_active = data.checkbox.is_active

        await self.controller_repository.commit()

    async def add_location(self, data: AddControllerLocationRequest) -> None:
        await self.identity_provider.ensure_superadmin()

        if not await self.location_repository.exists(data.location_id):
            raise LocationNotFoundError

        controller = await self._get_controller(data.controller_id)

        controller.location_id = data.location_id
        await self.controller_repository.commit()

    async def read_encashments(
        self, data: ReadEncashmentListRequest
    ) -> ReadEncashmentListResponse:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_location_admin(controller.location_id)

        encashments, total = await self.encashment_repository.get_list(data)

        return ReadEncashmentListResponse(
            encashments=[
                EncashmentScheme.model_validate(encashment)
                for encashment in encashments
            ],
            total=total,
        )

    async def close_encashment(self, data: CloseEncashmentRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_location_admin(controller.location_id)

        encashment = await self.encashment_repository.get(
            data.encashment_id, controller.id
        )
        if not encashment:
            raise EncashmentNotFoundError

        if encashment.is_closed:
            raise EncashmentAlreadyClosedError

        encashment.received_amount = data.received_amount
        encashment.is_closed = True

        await self.encashment_repository.commit()

    async def read_controller_public(
        self, data: ReadControllerRequest
    ) -> PublicWsmScheme | PublicCarwashScheme:
        controller = await self.controller_repository.get_concrete(data.controller_id)
        if not controller:
            raise ControllerNotFoundError

        if controller.type is ControllerType.CARWASH:
            return PublicCarwashScheme.make(controller)
        elif controller.type is ControllerType.WATER_VENDING:
            return PublicWsmScheme.make(controller)
        else:
            raise ValueError("This controller type is not supported yet")

    async def read_controller_list_public(
        self, data: ReadPublicControllerListRequest
    ) -> ReadPublicControllerListResponse:
        controllers, total = await self.controller_repository.get_list_concrete(
            data.location_id
        )

        controller_list = []
        for controller in controllers:
            if controller.type is ControllerType.CARWASH:
                controller_list.append(PublicCarwashScheme.make(controller))
            elif controller.type is ControllerType.WATER_VENDING:
                controller_list.append(PublicWsmScheme.make(controller))
            else:
                raise ValueError("This controller type is not supported yet")

        return ReadPublicControllerListResponse(
            controllers=controller_list, total=total
        )

    async def setup_tasmota(self, data: SetupTasmotaRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.company_id)

        if data.tasmota_id:
            configured_controller = await self.controller_repository.get_by_tasmota_id(
                data.tasmota_id
            )
            if configured_controller != controller:
                raise TasmotaIDAlreadyTakenError

        controller.tasmota_id = controller.tasmota_id
        await self.controller_repository.commit()

    async def edit_controller(self, data: EditControllerRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.company_id)

        dict_data = data.data.model_dump(exclude_unset=True)
        for k, v in dict_data.items():
            if hasattr(controller, k):
                setattr(controller, k, v)

        await self.controller_repository.commit()
