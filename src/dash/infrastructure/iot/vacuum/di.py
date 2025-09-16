from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.vacuum.client import (
    VacuumIoTClient,
    VacuumIoTDispatcher,
)
from dash.main.config import MqttConfig
from dash.presentation.iot_callbacks.begin import begin_callback
from dash.presentation.iot_callbacks.denomination import denomination_callback
from dash.presentation.iot_callbacks.state_info import state_info_callback
from dash.presentation.iot_callbacks.vacuum.encashment import (
    vacuum_encashment_callback,
)
from dash.presentation.iot_callbacks.vacuum.payment_card_get import (
    vacuum_payment_card_get_callback,
)
from dash.presentation.iot_callbacks.vacuum.sale import vacuum_sale_callback


async def get_vacuum_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[VacuumIoTClient]:
    async with VacuumIoTClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="car_vacuum_cleaner",
        dispatcher_class=VacuumIoTDispatcher,
        dispatcher_kwargs={"callback_kwargs": {"di_container": di_container}},
    ) as client:
        client.dispatcher.begin.register_callback(begin_callback)  # type: ignore
        client.dispatcher.state_info.register_callback(state_info_callback)  # type: ignore
        client.dispatcher.denomination.register_callback(denomination_callback)  # type: ignore
        client.dispatcher.sale.register_callback(vacuum_sale_callback)  # type: ignore
        client.dispatcher.payment_card_get.register_callback(
            vacuum_payment_card_get_callback,  # type: ignore
        )
        client.dispatcher.encashment.register_callback(vacuum_encashment_callback)  # type: ignore
        yield client
