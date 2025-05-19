from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.common.base_client import BaseDispatcher, BaseNpcClient
from dash.infrastructure.iot.wsm import WsmClient
from dash.main.config import MqttConfig
from dash.presentation.callbacks_wsm.state_info import state_info_callback


class CarwashClient(BaseNpcClient):
    pass


async def get_carwash_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[WsmClient]:
    async with WsmClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="car_wash",
        dispatcher=BaseDispatcher(callback_kwargs={"di_container": di_container}),
    ) as client:
        client.dispatcher.state_info.register_callback(state_info_callback)  # type: ignore
        yield client
