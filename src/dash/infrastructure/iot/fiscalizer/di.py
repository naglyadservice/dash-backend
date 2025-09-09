from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.common.base_client import BaseIoTDispatcher
from dash.infrastructure.iot.fiscalizer.client import FiscalizerIoTClient
from dash.main.config import MqttConfig
from dash.presentation.iot_callbacks.begin import begin_callback
from dash.presentation.iot_callbacks.fiscalizer.sale import fiscalizer_sale_callback
from dash.presentation.iot_callbacks.state_info import state_info_callback


async def get_fiscalizer_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[FiscalizerIoTClient]:
    async with FiscalizerIoTClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="fiscal",
        dispatcher_class=BaseIoTDispatcher,
        dispatcher_kwargs={"callback_kwargs": {"di_container": di_container}},
    ) as client:
        client.dispatcher.begin.register_callback(begin_callback)  # type: ignore
        client.dispatcher.state_info.register_callback(state_info_callback)  # type: ignore
        client.dispatcher.sale.register_callback(fiscalizer_sale_callback)  # type: ignore
        yield client
