from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.tasmota.client import TasmotaClient, TasmotaDispatcher
from dash.main.config import MqttConfig
from dash.presentation.iot_callbacks.tasmota import tasmota_callback


async def get_tasmota_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[TasmotaClient]:
    async with TasmotaClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="tele",
        dispatcher=TasmotaDispatcher(callback_kwargs={"di_container": di_container}),
    ) as client:
        client.dispatcher.state.register_callback(tasmota_callback)  # type: ignore
        yield client
