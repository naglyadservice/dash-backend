from dataclasses import dataclass
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses
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
    CheckboxCredentialsDTO,
    CloseEncashmentRequest,
    DeleteControllerRequest,
    EditControllerDTO,
    EditControllerRequest,
    GetEnergyStatsRequest,
    GetEnergyStatsResponse,
    LiqpayCredentialsDTO,
    LocationID,
    MonopayCredentialsDTO,
    ReadControllerListRequest,
    ReadPaginatedControllerListRequest,
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
from dash.services.controller.service import ControllerService

controller_router = APIRouter(
    prefix="/controllers",
    tags=["CONTROLLERS"],
    route_class=DishkaRoute,
)


@controller_router.get("", dependencies=[bearer_scheme])
async def read_controllers(
    controller_service: FromDishka[ControllerService],
    data: ReadPaginatedControllerListRequest = Depends(),
) -> ReadControllerResponse:
    return await controller_service.read_controllers(
        ReadControllerListRequest(**data.model_dump())
    )


@controller_router.post(
    "",
    dependencies=[bearer_scheme],
    responses=build_responses(
        (409, (DeviceIDAlreadyTakenError,)),
    ),
)
async def add_controller(
    controller_service: FromDishka[ControllerService],
    data: AddControllerRequest,
) -> AddControllerResponse:
    return await controller_service.add_controller(data)


@controller_router.post(
    "/{controller_id}",
    status_code=204,
    dependencies=[bearer_scheme],
    responses=build_responses((404, (ControllerNotFoundError, LocationNotFoundError))),
)
async def add_controller_location(
    controller_service: FromDishka[ControllerService],
    data: LocationID,
    controller_id: UUID,
) -> None:
    return await controller_service.add_location(
        AddControllerLocationRequest(
            controller_id=controller_id, location_id=data.location_id
        )
    )


@controller_router.post(
    "/{controller_id}/monopay",
    status_code=204,
    dependencies=[bearer_scheme],
)
async def add_monopay_credentials(
    controller_service: FromDishka[ControllerService],
    data: MonopayCredentialsDTO,
    controller_id: UUID,
) -> None:
    await controller_service.add_monopay_credentials(
        AddMonopayCredentialsRequest(controller_id=controller_id, monopay=data)
    )


@controller_router.post(
    "/{controller_id}/liqpay",
    status_code=204,
    dependencies=[bearer_scheme],
)
async def add_liqpay_credentials(
    controller_service: FromDishka[ControllerService],
    data: LiqpayCredentialsDTO,
    controller_id: UUID,
) -> None:
    await controller_service.add_liqpay_credentials(
        AddLiqpayCredentialsRequest(controller_id=controller_id, liqpay=data)
    )


@controller_router.post(
    "/{controller_id}/checkbox",
    status_code=204,
    dependencies=[bearer_scheme],
)
async def add_checkbox_credentials(
    controller_service: FromDishka[ControllerService],
    data: CheckboxCredentialsDTO,
    controller_id: UUID,
) -> None:
    await controller_service.add_checkbox_credentials(
        AddCheckboxCredentialsRequest(controller_id=controller_id, checkbox=data)
    )


@controller_router.get("/{controller_id}/encashments", dependencies=[bearer_scheme])
async def read_encashments(
    controller_service: FromDishka[ControllerService],
    data: ReadEncashmentListRequest = Depends(),
) -> ReadEncashmentListResponse:
    return await controller_service.read_encashments(data)


@dataclass
class EncashmentReceivedAmount:
    received_amount: int


@controller_router.post(
    "/{controller_id}/encashments/{encashment_id}",
    status_code=204,
    dependencies=[bearer_scheme],
    responses=build_responses(
        (404, (ControllerNotFoundError, EncashmentNotFoundError)),
        (409, (EncashmentAlreadyClosedError,)),
    ),
)
async def close_encashment(
    controller_service: FromDishka[ControllerService],
    controller_id: UUID,
    encashment_id: UUID,
    data: EncashmentReceivedAmount,
) -> None:
    await controller_service.close_encashment(
        CloseEncashmentRequest(
            controller_id=controller_id,
            encashment_id=encashment_id,
            received_amount=data.received_amount,
        )
    )


@controller_router.get("/public")
async def read_controller_list_public(
    controller_service: FromDishka[ControllerService],
    data: ReadPublicControllerListRequest = Depends(),
) -> ReadPublicControllerListResponse:
    return await controller_service.read_controller_list_public(data)


@controller_router.get("/public/{qr}")
async def read_controller_public(
    controller_service: FromDishka[ControllerService],
    data: ReadPublicControllerRequest = Depends(),
) -> ReadPublicControllerResponse:
    return await controller_service.read_controller_public(data)


@dataclass
class TasmotaID:
    tasmota_id: str | None


@controller_router.post(
    "/{controller_id}/tasmota",
    status_code=204,
    dependencies=[bearer_scheme],
    responses=build_responses((409, (TasmotaIDAlreadyTakenError,))),
)
async def setup_tasmota_electric_meter(
    controller_service: FromDishka[ControllerService],
    controller_id: UUID,
    data: TasmotaID,
) -> None:
    await controller_service.setup_tasmota(
        SetupTasmotaRequest(controller_id=controller_id, tasmota_id=data.tasmota_id)
    )


@controller_router.patch(
    "/{controller_id}",
    status_code=204,
    dependencies=[bearer_scheme],
)
async def edit_controller(
    controller_service: FromDishka[ControllerService],
    controller_id: UUID,
    data: EditControllerDTO,
) -> None:
    await controller_service.edit_controller(
        EditControllerRequest(controller_id=controller_id, data=data)
    )


@controller_router.get(
    "/{controller_id}/tasmota/statistics", dependencies=[bearer_scheme]
)
async def read_tasmota_stats(
    controller_service: FromDishka[ControllerService],
    data: GetEnergyStatsRequest = Depends(),
) -> GetEnergyStatsResponse:
    return await controller_service.read_energy_stats(data)


@dataclass
class MinDepositAmountDTO:
    amount: int


@controller_router.patch(
    "/{controller_id}/min-deposit-amount", status_code=204, dependencies=[bearer_scheme]
)
async def set_min_deposit_amount(
    controller_service: FromDishka[ControllerService],
    controller_id: UUID,
    data: MinDepositAmountDTO,
) -> None:
    await controller_service.set_min_deposit_amount(
        SetMinDepositAmountRequest(
            controller_id=controller_id, min_deposit_amount=data.amount
        )
    )


@controller_router.delete(
    "/{controller_id}", status_code=204, dependencies=[bearer_scheme]
)
async def delete_controller(
    controller_service: FromDishka[ControllerService],
    data: DeleteControllerRequest = Depends(),
) -> None:
    await controller_service.delete(data)
