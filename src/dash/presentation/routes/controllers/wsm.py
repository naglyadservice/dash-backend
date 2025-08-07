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
from dash.services.iot.wsm.dto import (
    SendWsmActionRequest,
    SetWsmConfigRequest,
    SetWsmSettingsRequest,
    WsmActionDTO,
    WsmConfig,
    WsmIoTControllerScheme,
    WsmSettings,
)
from dash.services.iot.wsm.service import WsmService

wsm_router = APIRouter(
    prefix="/wsm",
    tags=["WATER-VENDING"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@wsm_router.get(
    "/{controller_id}",
    responses=build_responses((404, (ControllerNotFoundError,))),
)
async def read_controller(
    wsm_service: FromDishka[WsmService],
    path: ControllerID = Depends(),
) -> WsmIoTControllerScheme:
    return await wsm_service.read_controller(path)


@wsm_router.patch(
    "/{controller_id}/config",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def update_config(
    wsm_service: FromDishka[WsmService],
    data: WsmConfig,
    controller_id: UUID,
) -> None:
    return await wsm_service.update_config(
        SetWsmConfigRequest(controller_id=controller_id, config=data)
    )


@wsm_router.patch(
    "/{controller_id}/settings",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def update_settings(
    wsm_service: FromDishka[WsmService],
    data: WsmSettings,
    controller_id: UUID,
) -> None:
    return await wsm_service.update_settings(
        SetWsmSettingsRequest(controller_id=controller_id, settings=data)
    )


@wsm_router.post(
    "/{controller_id}/actions",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_action(
    wsm_service: FromDishka[WsmService],
    data: WsmActionDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.send_action(
        SendWsmActionRequest(controller_id=controller_id, action=data)
    )


@wsm_router.post(
    "/{controller_id}/blocking",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def blocking(
    wsm_service: FromDishka[WsmService],
    data: BlockingDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.blocking(
        BlockingRequest(controller_id=controller_id, blocking=data.blocking)
    )


@wsm_router.post(
    "/{controller_id}/reboot",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def reboot_controller(
    wsm_service: FromDishka[WsmService],
    data: RebootDelayDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.reboot_controller(
        RebootControllerRequest(controller_id=controller_id, delay=data.delay)
    )


@wsm_router.post(
    "/{controller_id}/payments/qr",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_qr_payment(
    wsm_service: FromDishka[WsmService],
    data: QRPaymentDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.send_qr_payment(
        SendQRPaymentRequest(controller_id=controller_id, payment=data)
    )


@wsm_router.post(
    "/{controller_id}/payments/free",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_free_payment(
    wsm_service: FromDishka[WsmService],
    data: FreePaymentDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.send_free_payment(
        SendFreePaymentRequest(controller_id=controller_id, payment=data)
    )


@wsm_router.post(
    "/{controller_id}/payments/clear",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def clear_payments(
    wsm_service: FromDishka[WsmService],
    data: PaymentClearOptionsDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.clear_payments(
        ClearPaymentsRequest(controller_id=controller_id, options=data)
    )


@wsm_router.get(
    "/{controller_id}/display",
    responses=build_responses(*controller_errors),
)
async def get_display_info(
    wsm_service: FromDishka[WsmService],
    data: GetDisplayInfoRequest = Depends(),
):
    return await wsm_service.get_display(data)


class SyncWsmSettingsResponse(BaseModel):
    config: WsmConfig
    settings: WsmSettings


@wsm_router.patch(
    "/{controller_id}/sync",
    responses=build_responses(*controller_errors),
)
async def sync_settings(
    service: FromDishka[WsmService],
    data: SyncSettingsRequest = Depends(),
) -> SyncWsmSettingsResponse:
    return await service.sync_settings(data)  # type: ignore
