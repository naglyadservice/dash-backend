from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.car_cleaner.client import (
    CarCleanerIoTClient,
    CarCleanerIoTDispatcher,
)
from dash.main.config import MqttConfig
from dash.presentation.iot_callbacks.carwash.encashment import (
    carwash_encashment_callback,
)
from dash.presentation.iot_callbacks.car_cleaner.sale import car_cleaner_sale_callback
from dash.presentation.iot_callbacks.car_cleaner.payment_card_get import (
    car_cleaner_payment_card_get_callback,
)
from dash.presentation.iot_callbacks.denomination import denomination_callback
from dash.presentation.iot_callbacks.state_info import state_info_callback


async def get_car_cleaner_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[CarCleanerIoTClient]:
    async with CarCleanerIoTClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="car_dry_cleaning",
        dispatcher_class=CarCleanerIoTDispatcher,
        dispatcher_kwargs={"callback_kwargs": {"di_container": di_container}},
    ) as client:
        client.dispatcher.state_info.register_callback(state_info_callback)  # type: ignore
        client.dispatcher.denomination.register_callback(denomination_callback)  # type: ignore
        client.dispatcher.sale.register_callback(car_cleaner_sale_callback)  # type: ignore
        client.dispatcher.payment_card_get.register_callback(
            car_cleaner_payment_card_get_callback,  # type: ignore
        )
        client.dispatcher.encashment.register_callback(carwash_encashment_callback)  # type: ignore
        yield client
