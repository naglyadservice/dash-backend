from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses, controller_errors
from dash.services.common.errors.controller import ControllerNotFoundError
from dash.services.iot.car_cleaner.dto import (
    CarCleanerActionDTO,
    CarCleanerConfig,
    CarCleanerIoTControllerScheme,
    CarCleanerSettings,
    GetCarCleanerDisplayResponse,
    SendCarCleanerActionRequest,
    SetCarCleanerConfigRequest,
    SetCarCleanerSettingsRequest,
)
from dash.services.iot.car_cleaner.service import CarCleanerService
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

car_cleaner_router = APIRouter(
    prefix="/car_cleaner",
    tags=["CAR_CLEANER"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@car_cleaner_router.get(
    "/{controller_id}",
    responses=build_responses((404, (ControllerNotFoundError,))),
)
async def read_controller(
    service: FromDishka[CarCleanerService],
    data: ControllerID = Depends(),
) -> CarCleanerIoTControllerScheme:
    return await service.read_controller(data)


@car_cleaner_router.patch(
    "/{controller_id}/config",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def update_config(
    service: FromDishka[CarCleanerService],
    data: CarCleanerConfig,
    controller_id: UUID,
) -> None:
    await service.update_config(
        SetCarCleanerConfigRequest(controller_id=controller_id, config=data)
    )


@car_cleaner_router.patch(
    "/{controller_id}/settings",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def update_settings(
    service: FromDishka[CarCleanerService],
    data: CarCleanerSettings,
    controller_id: UUID,
) -> None:
    await service.update_settings(
        SetCarCleanerSettingsRequest(controller_id=controller_id, settings=data)
    )


@car_cleaner_router.post(
    "/{controller_id}/actions",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_action(
    service: FromDishka[CarCleanerService],
    data: CarCleanerActionDTO,
    controller_id: UUID,
) -> None:
    await service.send_action(
        SendCarCleanerActionRequest(controller_id=controller_id, action=data)
    )


@car_cleaner_router.post(
    "/{controller_id}/blocking",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def blocking(
    service: FromDishka[CarCleanerService],
    data: BlockingDTO,
    controller_id: UUID,
) -> None:
    await service.blocking(
        BlockingRequest(controller_id=controller_id, blocking=data.blocking)
    )


@car_cleaner_router.post(
    "/{controller_id}/reboot",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def reboot_controller(
    service: FromDishka[CarCleanerService],
    data: RebootDelayDTO,
    controller_id: UUID,
) -> None:
    await service.reboot_controller(
        RebootControllerRequest(controller_id=controller_id, delay=data.delay)
    )


@car_cleaner_router.post(
    "/{controller_id}/payments/qr",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_qr_payment(
    service: FromDishka[CarCleanerService],
    data: QRPaymentDTO,
    controller_id: UUID,
) -> None:
    await service.send_qr_payment(
        SendQRPaymentRequest(controller_id=controller_id, payment=data)
    )


@car_cleaner_router.post(
    "/{controller_id}/payments/free",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def send_free_payment(
    service: FromDishka[CarCleanerService],
    data: FreePaymentDTO,
    controller_id: UUID,
) -> None:
    await service.send_free_payment(
        SendFreePaymentRequest(controller_id=controller_id, payment=data)
    )


@car_cleaner_router.post(
    "/{controller_id}/payments/clear",
    status_code=204,
    responses=build_responses(*controller_errors),
)
async def clear_payments(
    service: FromDishka[CarCleanerService],
    data: PaymentClearOptionsDTO,
    controller_id: UUID,
) -> None:
    await service.clear_payments(
        ClearPaymentsRequest(controller_id=controller_id, options=data)
    )


@car_cleaner_router.get(
    "/{controller_id}/display",
    responses=build_responses(*controller_errors),
)
async def get_display_info(
    service: FromDishka[CarCleanerService],
    data: GetDisplayInfoRequest = Depends(),
) -> GetCarCleanerDisplayResponse:
    return await service.get_display_info(data)


class SyncCarCleanerSettingsResponse(BaseModel):
    config: CarCleanerConfig
    settings: CarCleanerSettings


@car_cleaner_router.patch(
    "/{controller_id}/sync",
    responses=build_responses(*controller_errors),
)
async def sync_settings(
    service: FromDishka[CarCleanerService],
    data: SyncSettingsRequest = Depends(),
) -> SyncCarCleanerSettingsResponse:
    return await service.sync_settings(data)  # type: ignore
