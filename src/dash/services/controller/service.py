from typing import Sequence
from uuid import UUID

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.encashment import EncashmentRepository
from dash.infrastructure.repositories.energy_state import EnergyStateRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.models.admin_user import AdminRole, AdminUser
from dash.models.controllers.carwash import CarwashController
from dash.models.controllers.controller import Controller, ControllerType
from dash.models.controllers.fiscalizer import FiscalizerController
from dash.models.controllers.vacuum import VacuumController
from dash.models.controllers.water_vending import WaterVendingController
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.dto import PublicCompanyDTO, PublicLocationDTO
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    DeviceIDAlreadyTakenError,
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
    GetEnergyStatsRequest,
    GetEnergyStatsResponse,
    PublicCarwashScheme,
    PublicFiscalizerScheme,
    PublicWsmScheme,
    ReadControllerListRequest,
    ReadControllerResponse,
    ReadEncashmentListRequest,
    ReadEncashmentListResponse,
    ReadPublicControllerListRequest,
    ReadPublicControllerListResponse,
    ReadPublicControllerRequest,
    ReadPublicControllerResponse,
    SetMinDepositAmountRequest,
    SetupTasmotaRequest,
)
from dash.services.controller.utils import generate_qr
from dash.services.iot.factory import IoTServiceFactory


class ControllerService:
    def __init__(
        self,
        identity_provider: IdProvider,
        controller_repository: ControllerRepository,
        location_repository: LocationRepository,
        energy_repository: EnergyStateRepository,
        encashment_repository: EncashmentRepository,
        factory: IoTServiceFactory,
        check_online_interactor: CheckOnlineInteractor,
    ):
        self.identity_provider = identity_provider
        self.controller_repository = controller_repository
        self.location_repository = location_repository
        self.energy_repository = energy_repository
        self.encashment_repository = encashment_repository
        self.factory = factory
        self.check_online = check_online_interactor

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
                ControllerScheme.make(controller, await self.check_online(controller))
                for controller in controllers
            ],
            total=total,
        )

    async def add_controller(self, data: AddControllerRequest) -> AddControllerResponse:
        await self.identity_provider.ensure_superadmin()

        existing_controller = await self.controller_repository.get_by_device_id(
            data.device_id
        )
        if existing_controller is not None:
            raise DeviceIDAlreadyTakenError

        controller_dict = data.model_dump()
        qr = await self._generate_unique_qr(data.type)

        if data.type is ControllerType.WATER_VENDING:
            controller = WaterVendingController(**controller_dict, qr=qr)

        if data.type is ControllerType.CARWASH:
            controller = CarwashController(**controller_dict, qr=qr)

        if data.type is ControllerType.VACUUM:
            controller = VacuumController(**controller_dict, qr=qr)

        if data.type is ControllerType.FISCALIZER:
            controller = FiscalizerController(**controller_dict, qr=qr)

        await self.factory.get(controller.type).sync_settings_infra(controller)

        self.controller_repository.add(controller)
        await self.controller_repository.commit()

        return AddControllerResponse(id=controller.id)

    async def _generate_unique_qr(self, controller_type: ControllerType) -> str:
        qr = generate_qr(controller_type)
        while await self.controller_repository.exists_by_qr(qr):
            qr = generate_qr(controller_type)

        return qr

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
        controller.fiscalize_cash = data.checkbox.fiscalize_cash

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
        self, data: ReadPublicControllerRequest
    ) -> ReadPublicControllerResponse:
        controller = await self.controller_repository.get_concrete_by_qr(data.qr)
        if not controller:
            raise ControllerNotFoundError

        if controller.type is ControllerType.CARWASH:
            controller_scheme = PublicCarwashScheme.model_validate(controller)
        elif controller.type is ControllerType.WATER_VENDING:
            controller_scheme = PublicWsmScheme.model_validate(controller)
        elif controller.type is ControllerType.FISCALIZER:
            controller_scheme = PublicFiscalizerScheme.model_validate(controller)
        else:
            raise ValueError("This controller type is not supported yet")

        return ReadPublicControllerResponse(
            company=controller.company
            and PublicCompanyDTO.model_validate(controller.company),
            location=controller.location
            and PublicLocationDTO.model_validate(controller.location),
            controller=controller_scheme,
        )

    async def read_controller_list_public(
        self, data: ReadPublicControllerListRequest
    ) -> ReadPublicControllerListResponse:
        controllers, total = await self.controller_repository.get_list_concrete(
            data.location_id
        )
        location = await self.location_repository.get(data.location_id)
        if not location:
            raise LocationNotFoundError

        controller_list = []
        for controller in controllers:
            if controller.type is ControllerType.CARWASH:
                controller_list.append(PublicCarwashScheme.model_validate(controller))
            elif controller.type is ControllerType.WATER_VENDING:
                controller_list.append(PublicWsmScheme.model_validate(controller))
            elif controller.type is ControllerType.FISCALIZER:
                controller_list.append(
                    PublicFiscalizerScheme.model_validate(controller)
                )
            else:
                raise ValueError("This controller type is not supported yet")

        return ReadPublicControllerListResponse(
            company=location.company
            and PublicCompanyDTO.model_validate(location.company),
            location=PublicLocationDTO.model_validate(location),
            controllers=controller_list,
        )

    async def setup_tasmota(self, data: SetupTasmotaRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_company_owner(controller.company_id)

        if data.tasmota_id:
            configured_controller = await self.controller_repository.get_by_tasmota_id(
                data.tasmota_id
            )
            if configured_controller and configured_controller != controller:
                raise TasmotaIDAlreadyTakenError

        controller.tasmota_id = data.tasmota_id
        await self.controller_repository.commit()

    async def set_min_deposit_amount(self, data: SetMinDepositAmountRequest) -> None:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_company_owner(controller.company_id)

        controller.min_deposit_amount = data.min_deposit_amount
        await self.controller_repository.commit()

    async def edit_controller(self, data: EditControllerRequest) -> None:
        controller = await self._get_controller(data.controller_id)

        await self.identity_provider.ensure_company_owner(controller.company_id)

        dict_data = data.data.model_dump(exclude_unset=True)
        for k, v in dict_data.items():
            if hasattr(controller, k):
                setattr(controller, k, v)

        await self.controller_repository.commit()

    async def read_energy_stats(
        self, data: GetEnergyStatsRequest
    ) -> GetEnergyStatsResponse:
        controller = await self._get_controller(data.controller_id)
        await self.identity_provider.ensure_location_admin(controller.location_id)

        return await self.energy_repository.get_stats(data)
