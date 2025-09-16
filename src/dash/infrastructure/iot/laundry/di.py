from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.laundry.client import (
    LaundryIoTClient,
    LaundryIoTDispatcher,
)
from dash.main.config import MqttConfig
from dash.presentation.iot_callbacks.begin import begin_callback
from dash.presentation.iot_callbacks.laundry.state_info import (
    laundry_state_info_callback,
)


async def get_laundry_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[LaundryIoTClient]:
    async with LaundryIoTClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="v2",
        dispatcher_class=LaundryIoTDispatcher,
        dispatcher_kwargs={"callback_kwargs": {"di_container": di_container}},
    ) as client:
        client.dispatcher.begin.register_callback(begin_callback)  # type: ignore
        client.dispatcher.state_info.register_callback(laundry_state_info_callback)  # type: ignore
        yield client
