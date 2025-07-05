from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.iot.dto import (
    ControllerID,
    FreePaymentDTO,
    RebootControllerRequest,
    RebootDelayDTO,
    SendFreePaymentRequest,
)
from dash.services.iot.fiscalizer.dto import (
    FiscalizerConfig,
    FiscalizerIoTControllerScheme,
    FiscalizerSettings,
    QuickDepositButtonsDTO,
    SetFiscalizerConfigRequest,
    SetFiscalizerSettingsRequest,
    SetupQuickDepositButtonsRequest,
)
from dash.services.iot.fiscalizer.service import FiscalizerService

fiscalizer_router = APIRouter(
    prefix="/fiscalizer",
    tags=["FISCALIZER"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@fiscalizer_router.get("/{controller_id}")
async def read_controller(
    service: FromDishka[FiscalizerService],
    data: ControllerID = Depends(),
) -> FiscalizerIoTControllerScheme:
    return await service.read_controller(data)


@fiscalizer_router.patch("/{controller_id}/config", status_code=204)
async def update_config(
    service: FromDishka[FiscalizerService],
    data: FiscalizerConfig,
    controller_id: UUID,
) -> None:
    await service.update_config(
        SetFiscalizerConfigRequest(controller_id=controller_id, config=data)
    )


@fiscalizer_router.patch("/{controller_id}/settings", status_code=204)
async def update_settings(
    service: FromDishka[FiscalizerService],
    data: FiscalizerSettings,
    controller_id: UUID,
) -> None:
    await service.update_settings(
        SetFiscalizerSettingsRequest(controller_id=controller_id, settings=data)
    )


@fiscalizer_router.post("/{controller_id}/reboot", status_code=204)
async def reboot_controller(
    service: FromDishka[FiscalizerService],
    data: RebootDelayDTO,
    controller_id: UUID,
) -> None:
    await service.reboot_controller(
        RebootControllerRequest(controller_id=controller_id, delay=data.delay)
    )


@fiscalizer_router.post("/{controller_id}/payments/free", status_code=204)
async def send_free_payment(
    service: FromDishka[FiscalizerService],
    data: FreePaymentDTO,
    controller_id: UUID,
) -> None:
    await service.send_free_payment(
        SendFreePaymentRequest(controller_id=controller_id, payment=data)
    )


@fiscalizer_router.patch("/{controller_id}/quick-deposit-buttons", status_code=204)
async def update_quick_deposit_buttons(
    service: FromDishka[FiscalizerService],
    data: QuickDepositButtonsDTO,
    controller_id: UUID,
) -> None:
    await service.setup_quick_deposit_buttons(
        SetupQuickDepositButtonsRequest(controller_id=controller_id, buttons=data)
    )
