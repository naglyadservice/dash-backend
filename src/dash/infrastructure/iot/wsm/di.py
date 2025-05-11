from typing import AsyncIterator

from dishka import AsyncContainer

from dash.main.config import MqttConfig
from dash.presentation.callbacks_wsm.denomination import denomination_callback
from dash.presentation.callbacks_wsm.sale import sale_callback
from dash.presentation.callbacks_wsm.state_info import state_info_callback

from .client import WsmClient, WsmDispatcher


async def get_npc_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[WsmClient]:
    async with WsmClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="wsm",
        dispatcher=WsmDispatcher(callback_kwargs={"di_container": di_container}),
    ) as client:
        client.dispatcher.state_info.register_callback(state_info_callback)  # type: ignore
        client.dispatcher.sale.register_callback(sale_callback)  # type: ignore
        client.dispatcher.denomination.register_callback(denomination_callback)  # type: ignore
        yield client
