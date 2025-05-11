from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.water_vending.dto import (
    ClearPaymentsRequest,
    ControllerID,
    FreePaymentDTO,
    GetDisplayInfoRequest,
    PaymentClearOptionsDTO,
    QRPaymentDTO,
    RebootControllerRequest,
    SendActionRequest,
    SendFreePaymentRequest,
    SendQRPaymentRequest,
    SetWaterVendingConfigRequest,
    SetWaterVendingSettingsRequest,
    WaterVendingActionDTO,
    WaterVendingConfig,
    WaterVendingControllerScheme,
    WaterVendingSettings,
)
from dash.services.water_vending.water_vending import WaterVendingService

water_vending_router = APIRouter(
    prefix="/water-vending",
    tags=["WATER-VENDING"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@water_vending_router.get("/{controller_id}")
async def read_controller(
    water_vending_service: FromDishka[WaterVendingService],
    path: ControllerID = Depends(),
) -> WaterVendingControllerScheme:
    return await water_vending_service.read_controller(path)


@water_vending_router.post("/{controller_id}/config", status_code=204)
async def set_config(
    water_vending_service: FromDishka[WaterVendingService],
    data: WaterVendingConfig,
    controller_id: UUID,
) -> None:
    return await water_vending_service.set_config(
        SetWaterVendingConfigRequest(controller_id=controller_id, config=data)
    )


@water_vending_router.post("/{controller_id}/settings", status_code=204)
async def set_settings(
    water_vending_service: FromDishka[WaterVendingService],
    data: WaterVendingSettings,
    controller_id: UUID,
) -> None:
    return await water_vending_service.set_settings(
        SetWaterVendingSettingsRequest(controller_id=controller_id, settings=data)
    )


@water_vending_router.post("/{controller_id}/actions", status_code=204)
async def send_action(
    water_vending_service: FromDishka[WaterVendingService],
    data: WaterVendingActionDTO,
    controller_id: UUID,
) -> None:
    return await water_vending_service.send_action(
        SendActionRequest(controller_id=controller_id, actions=data)
    )


@water_vending_router.post("/{controller_id}/reboot", status_code=204)
async def reboot_controller(
    water_vending_service: FromDishka[WaterVendingService],
    data: RebootControllerRequest = Depends(),
) -> None:
    return await water_vending_service.reboot_controller(data)


@water_vending_router.post("/{controller_id}/payments/qr", status_code=204)
async def send_qr_payment(
    water_vending_service: FromDishka[WaterVendingService],
    data: QRPaymentDTO,
    controller_id: UUID,
) -> None:
    return await water_vending_service.send_qr_payment(
        SendQRPaymentRequest(controller_id=controller_id, payment=data)
    )


@water_vending_router.post("/{controller_id}/payments/free", status_code=204)
async def send_free_payment(
    water_vending_service: FromDishka[WaterVendingService],
    data: FreePaymentDTO,
    controller_id: UUID,
) -> None:
    return await water_vending_service.send_free_payment(
        SendFreePaymentRequest(controller_id=controller_id, payment=data)
    )


@water_vending_router.post("/{controller_id}/payments/clear", status_code=204)
async def clear_payments(
    water_vending_service: FromDishka[WaterVendingService],
    data: PaymentClearOptionsDTO,
    controller_id: UUID,
) -> None:
    return await water_vending_service.clear_payments(
        ClearPaymentsRequest(controller_id=controller_id, options=data)
    )


@water_vending_router.get("/{controller_id}/display")
async def get_display_info(
    water_vending_service: FromDishka[WaterVendingService],
    data: GetDisplayInfoRequest = Depends(),
):
    return await water_vending_service.get_display(data)
