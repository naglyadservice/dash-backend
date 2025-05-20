from dataclasses import dataclass
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.iot.dto import (
    ClearPaymentsRequest,
    ControllerID,
    FreePaymentDTO,
    GetDisplayInfoRequest,
    PaymentClearOptionsDTO,
    QRPaymentDTO,
    RebootControllerRequest,
    SendFreePaymentRequest,
    SendQRPaymentRequest,
)
from dash.services.iot.wsm.dto import (
    SendWsmActionRequest,
    SetWsmConfigRequest,
    SetWsmSettingsRequest,
    WsmActionDTO,
    WsmConfig,
    WsmControllerScheme,
    WsmSettings,
)
from dash.services.iot.wsm.service import WsmService

wsm_router = APIRouter(
    prefix="/wsm",
    tags=["WATER-VENDING"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@wsm_router.get("/{controller_id}")
async def read_controller(
    wsm_service: FromDishka[WsmService],
    path: ControllerID = Depends(),
) -> WsmControllerScheme:
    return await wsm_service.read_controller(path)


@wsm_router.post("/{controller_id}/config", status_code=204)
async def set_config(
    wsm_service: FromDishka[WsmService],
    data: WsmConfig,
    controller_id: UUID,
) -> None:
    return await wsm_service.set_config(
        SetWsmConfigRequest(controller_id=controller_id, config=data)
    )


@wsm_router.post("/{controller_id}/settings", status_code=204)
async def set_settings(
    wsm_service: FromDishka[WsmService],
    data: WsmSettings,
    controller_id: UUID,
) -> None:
    return await wsm_service.set_settings(
        SetWsmSettingsRequest(controller_id=controller_id, settings=data)
    )


@wsm_router.post("/{controller_id}/actions", status_code=204)
async def send_action(
    wsm_service: FromDishka[WsmService],
    data: WsmActionDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.send_action(
        SendWsmActionRequest(controller_id=controller_id, action=data)
    )


@dataclass
class DelayDTO:
    delay: int


@wsm_router.post("/{controller_id}/reboot", status_code=204)
async def reboot_controller(
    wsm_service: FromDishka[WsmService],
    data: DelayDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.reboot_controller(
        RebootControllerRequest(controller_id=controller_id, delay=data.delay)
    )


@wsm_router.post("/{controller_id}/payments/qr", status_code=204)
async def send_qr_payment(
    wsm_service: FromDishka[WsmService],
    data: QRPaymentDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.send_qr_payment(
        SendQRPaymentRequest(controller_id=controller_id, payment=data)
    )


@wsm_router.post("/{controller_id}/payments/free", status_code=204)
async def send_free_payment(
    wsm_service: FromDishka[WsmService],
    data: FreePaymentDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.send_free_payment(
        SendFreePaymentRequest(controller_id=controller_id, payment=data)
    )


@wsm_router.post("/{controller_id}/payments/clear", status_code=204)
async def clear_payments(
    wsm_service: FromDishka[WsmService],
    data: PaymentClearOptionsDTO,
    controller_id: UUID,
) -> None:
    return await wsm_service.clear_payments(
        ClearPaymentsRequest(controller_id=controller_id, options=data)
    )


@wsm_router.get("/{controller_id}/display")
async def get_display_info(
    wsm_service: FromDishka[WsmService],
    data: GetDisplayInfoRequest = Depends(),
):
    return await wsm_service.get_display(data)
