from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.iot.carwash.dto import (
    CarwashActionDTO,
    CarwashConfig,
    CarwashIoTControllerScheme,
    CarwashSettings,
    GetCarwashDisplayResponse,
    SendCarwashActionRequest,
    SetCarwashConfigRequest,
    SetCarwashSettingsRequest,
)
from dash.services.iot.carwash.service import CarwashService
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
)

carwash_router = APIRouter(
    prefix="/carwash",
    tags=["CARWASH"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@carwash_router.get("/{controller_id}")
async def read_controller(
    service: FromDishka[CarwashService],
    data: ControllerID = Depends(),
) -> CarwashIoTControllerScheme:
    return await service.read_controller(data)


@carwash_router.patch("/{controller_id}/config", status_code=204)
async def update_config(
    service: FromDishka[CarwashService],
    data: CarwashConfig,
    controller_id: UUID,
) -> None:
    await service.update_config(
        SetCarwashConfigRequest(controller_id=controller_id, config=data)
    )


@carwash_router.patch("/{controller_id}/settings", status_code=204)
async def update_settings(
    service: FromDishka[CarwashService],
    data: CarwashSettings,
    controller_id: UUID,
) -> None:
    await service.update_settings(
        SetCarwashSettingsRequest(controller_id=controller_id, settings=data)
    )


@carwash_router.post("/{controller_id}/actions", status_code=204)
async def send_action(
    service: FromDishka[CarwashService],
    data: CarwashActionDTO,
    controller_id: UUID,
) -> None:
    await service.send_action(
        SendCarwashActionRequest(controller_id=controller_id, action=data)
    )


@carwash_router.post("/{controller_id}/blocking", status_code=204)
async def blocking(
    service: FromDishka[CarwashService],
    data: BlockingDTO,
    controller_id: UUID,
) -> None:
    await service.blocking(
        BlockingRequest(controller_id=controller_id, blocking=data.blocking)
    )


@carwash_router.post("/{controller_id}/reboot", status_code=204)
async def reboot_controller(
    service: FromDishka[CarwashService],
    data: RebootDelayDTO,
    controller_id: UUID,
) -> None:
    await service.reboot_controller(
        RebootControllerRequest(controller_id=controller_id, delay=data.delay)
    )


@carwash_router.post("/{controller_id}/payments/qr", status_code=204)
async def send_qr_payment(
    service: FromDishka[CarwashService],
    data: QRPaymentDTO,
    controller_id: UUID,
) -> None:
    await service.send_qr_payment(
        SendQRPaymentRequest(controller_id=controller_id, payment=data)
    )


@carwash_router.post("/{controller_id}/payments/free", status_code=204)
async def send_free_payment(
    service: FromDishka[CarwashService],
    data: FreePaymentDTO,
    controller_id: UUID,
) -> None:
    await service.send_free_payment(
        SendFreePaymentRequest(controller_id=controller_id, payment=data)
    )


@carwash_router.post("/{controller_id}/payments/clear", status_code=204)
async def clear_payments(
    service: FromDishka[CarwashService],
    data: PaymentClearOptionsDTO,
    controller_id: UUID,
) -> None:
    await service.clear_payments(
        ClearPaymentsRequest(controller_id=controller_id, options=data)
    )


@carwash_router.get("/{controller_id}/display")
async def get_display_info(
    service: FromDishka[CarwashService],
    data: GetDisplayInfoRequest = Depends(),
) -> GetCarwashDisplayResponse:
    return await service.get_display(data)
