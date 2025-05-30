from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.mqtt.client import MqttClient, MqttDispatcher
from dash.main.config import MqttConfig
from dash.presentation.iot_callbacks.tasmota import tasmota_callback


async def get_mqtt_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[MqttClient]:
    async with MqttClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="",
        dispatcher_class=MqttDispatcher,
        dispatcher_kwargs={"callback_kwargs": {"di_container": di_container}},
    ) as client:
        client.dispatcher.tasmota_state.register_callback(tasmota_callback)  # type: ignore
        yield client
