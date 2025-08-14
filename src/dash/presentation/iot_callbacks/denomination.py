from dataclasses import dataclass
from datetime import datetime

from adaptix import Retort
from ddtrace.trace import tracer
from dishka import FromDishka
from structlog import get_logger

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.presentation.iot_callbacks.common.di_injector import (
    datetime_recipe,
    inject,
    parse_payload,
    request_scope,
)

logger = get_logger()


@dataclass
class DenominationCallbackPayload:
    created: datetime
    coin: int | None = None
    bill: int | None = None


denomination_callback_retort = Retort(recipe=[*datetime_recipe])


@tracer.wrap()
@parse_payload(retort=denomination_callback_retort)
@request_scope
@inject
async def denomination_callback(
    device_id: str,
    data: DenominationCallbackPayload,
    controller_repository: FromDishka[ControllerRepository],
    payment_repository: FromDishka[PaymentRepository],
    checkbox_service: FromDishka[CheckboxService],
) -> None:
    dict_data = denomination_callback_retort.dump(data)
    controller = await controller_repository.get_by_device_id(device_id)

    logger.info(
        "Denomination request received",
        device_id=device_id,
        data=dict_data,
    )
