from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses, controller_errors
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.iot.dto import (
    BlockingDTO,
    BlockingRequest,
    ClearPaymentsRequest,
    ControllerID,
    FreePaymentDTO,
    GetDisplayInfoRequest,
    PaymentClearOptionsDTO,
    QRPaymentDTO,
    RebootControllerRequest,
    RebootDelayDTO,
    SendFreePaymentRequest,
    SendQRPaymentRequest,
    SyncSettingsRequest,
)
from dash.services.iot.vacuum.dto import (
    GetVacuumDisplayResponse,
    SendVacuumActionRequest,
    SetVacuumConfigRequest,
    SetVacuumSettingsRequest,
    VacuumActionDTO,
    VacuumConfig,
    VacuumIoTControllerScheme,
    VacuumSettings,
)
from dash.services.iot.vacuum.service import VacuumService

vacuum_router = APIRouter(
    prefix="/vacuum",
    tags=["VACUUM"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@vacuum_router.get(
    "/{controller_id}",
    responses=build_responses((404, (ControllerNotFoundError,))),
)
async def read_controller(
    service: FromDishka[VacuumService],
    data: ControllerID = Depends(),
) -> VacuumIoTControllerScheme:
    return await service.read_controller(data)


@vacuum_router.patch(
    "/{controller_id}/config",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def update_config(
    service: FromDishka[VacuumService],
    data: VacuumConfig,
    controller_id: UUID,
) -> None:
    await service.update_config(
        SetVacuumConfigRequest(controller_id=controller_id, config=data)
    )


@vacuum_router.patch(
    "/{controller_id}/settings",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def update_settings(
    service: FromDishka[VacuumService],
    data: VacuumSettings,
    controller_id: UUID,
) -> None:
    await service.update_settings(
        SetVacuumSettingsRequest(controller_id=controller_id, settings=data)
    )


@vacuum_router.post(
    "/{controller_id}/actions",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_action(
    service: FromDishka[VacuumService],
    data: VacuumActionDTO,
    controller_id: UUID,
) -> None:
    await service.send_action(
        SendVacuumActionRequest(controller_id=controller_id, action=data)
    )


@vacuum_router.post(
    "/{controller_id}/blocking",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def blocking(
    service: FromDishka[VacuumService],
    data: BlockingDTO,
    controller_id: UUID,
) -> None:
    await service.blocking(
        BlockingRequest(controller_id=controller_id, blocking=data.blocking)
    )


@vacuum_router.post(
    "/{controller_id}/reboot",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def reboot_controller(
    service: FromDishka[VacuumService],
    data: RebootDelayDTO,
    controller_id: UUID,
) -> None:
    await service.reboot_controller(
        RebootControllerRequest(controller_id=controller_id, delay=data.delay)
    )


@vacuum_router.post(
    "/{controller_id}/payments/qr",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_qr_payment(
    service: FromDishka[VacuumService],
    data: QRPaymentDTO,
    controller_id: UUID,
) -> None:
    await service.send_qr_payment(
        SendQRPaymentRequest(controller_id=controller_id, payment=data)
    )


@vacuum_router.post(
    "/{controller_id}/payments/free",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_free_payment(
    service: FromDishka[VacuumService],
    data: FreePaymentDTO,
    controller_id: UUID,
) -> None:
    await service.send_free_payment(
        SendFreePaymentRequest(controller_id=controller_id, payment=data)
    )


@vacuum_router.post(
    "/{controller_id}/payments/clear",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def clear_payments(
    service: FromDishka[VacuumService],
    data: PaymentClearOptionsDTO,
    controller_id: UUID,
) -> None:
    await service.clear_payments(
        ClearPaymentsRequest(controller_id=controller_id, options=data)
    )


@vacuum_router.get(
    "/{controller_id}/display",
    responses=build_responses(*controller_errors),
)
async def get_display_info(
    service: FromDishka[VacuumService],
    data: GetDisplayInfoRequest = Depends(),
) -> GetVacuumDisplayResponse:
    return await service.get_display(data)


class SyncVacuumSettingsResponse(BaseModel):
    config: VacuumConfig
    settings: VacuumSettings


@vacuum_router.patch(
    "/{controller_id}/sync",
    responses=build_responses(*controller_errors),
)
async def sync_settings(
    service: FromDishka[VacuumService],
    data: SyncSettingsRequest = Depends(),
) -> SyncVacuumSettingsResponse:
    return await service.sync_settings(data)  # type: ignore
