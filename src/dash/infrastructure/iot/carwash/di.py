from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.carwash.client import CarwashClient
from dash.infrastructure.iot.common.base_client import BaseDispatcher
from dash.main.config import MqttConfig
from dash.presentation.iot_callbacks.carwash.encashment import (
    carwash_encashment_callback,
)
from dash.presentation.iot_callbacks.carwash.payment_card_get import (
    carwash_payment_card_get_callback,
)
from dash.presentation.iot_callbacks.carwash.sale import carwash_sale_callback
from dash.presentation.iot_callbacks.denomination import denomination_callback
from dash.presentation.iot_callbacks.state_info import state_info_callback


async def get_carwash_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[CarwashClient]:
    async with CarwashClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="car_wash",
        dispatcher=BaseDispatcher(callback_kwargs={"di_container": di_container}),
    ) as client:
        client.dispatcher.state_info.register_callback(state_info_callback)  # type: ignore
        client.dispatcher.denomination.register_callback(denomination_callback)  # type: ignore
        client.dispatcher.sale.register_callback(carwash_sale_callback)  # type: ignore
        client.dispatcher.payment_card_get.register_callback(
            carwash_payment_card_get_callback
        )  # type: ignore
        client.dispatcher.encashment.register_callback(carwash_encashment_callback)  # type: ignore
        yield client
