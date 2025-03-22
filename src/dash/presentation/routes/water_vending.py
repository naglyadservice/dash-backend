from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.services.water_vending.dto import (
    ClearPaymentsRequest,
    ControllerID,
    FreePaymentRequest,
    PaymentClearOptionsDTO,
    QRPaymentRequest,
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
    prefix="/water-vending", tags=["WATER-VENDING"], route_class=DishkaRoute
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
    body: WaterVendingConfig,
    path: ControllerID = Depends(),
) -> None:
    return await water_vending_service.set_config(
        SetWaterVendingConfigRequest(controller_id=path.controller_id, config=body)
    )


@water_vending_router.post("/{controller_id}/settings", status_code=204)
async def set_settings(
    water_vending_service: FromDishka[WaterVendingService],
    body: WaterVendingSettings,
    path: ControllerID = Depends(),
) -> None:
    return await water_vending_service.set_settings(
        SetWaterVendingSettingsRequest(controller_id=path.controller_id, settings=body)
    )


@water_vending_router.post("/{controller_id}/actions", status_code=204)
async def send_action(
    water_vending_service: FromDishka[WaterVendingService],
    body: WaterVendingActionDTO,
    path: ControllerID = Depends(),
) -> None:
    return await water_vending_service.send_action(
        SendActionRequest(controller_id=path.controller_id, actions=body)
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
    body: QRPaymentRequest,
    path: ControllerID = Depends(),
) -> None:
    return await water_vending_service.send_qr_payment(
        SendQRPaymentRequest(controller_id=path.controller_id, **body.model_dump())
    )


@water_vending_router.post("/{controller_id}/payments/free", status_code=204)
async def send_free_payment(
    water_vending_service: FromDishka[WaterVendingService],
    body: FreePaymentRequest,
    path: ControllerID = Depends(),
) -> None:
    return await water_vending_service.send_free_payment(
        SendFreePaymentRequest(controller_id=path.controller_id, amount=body.amount)
    )


@water_vending_router.post("/{controller_id}/payments/clear", status_code=204)
async def clear_payments(
    water_vending_service: FromDishka[WaterVendingService],
    data: PaymentClearOptionsDTO,
    path: ControllerID = Depends(),
) -> None:
    return await water_vending_service.clear_payments(
        ClearPaymentsRequest(controller_id=path.controller_id, options=data)
    )
