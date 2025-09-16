from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.common.base_client import BaseIoTDispatcher
from dash.infrastructure.iot.wsm.client import WsmIoTClient
from dash.main.config import MqttConfig
from dash.presentation.iot_callbacks.begin import begin_callback
from dash.presentation.iot_callbacks.denomination import denomination_callback
from dash.presentation.iot_callbacks.state_info import state_info_callback
from dash.presentation.iot_callbacks.wsm.encashment import wsm_encashment_callback
from dash.presentation.iot_callbacks.wsm.payment_card_get import (
    wsm_payment_card_get_callback,
)
from dash.presentation.iot_callbacks.wsm.sale import wsm_sale_callback


async def get_wsm_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[WsmIoTClient]:
    async with WsmIoTClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="wsm",
        dispatcher_class=BaseIoTDispatcher,
        dispatcher_kwargs={"callback_kwargs": {"di_container": di_container}},
    ) as client:
        client.dispatcher.begin.register_callback(begin_callback)  # type: ignore
        client.dispatcher.state_info.register_callback(state_info_callback)  # type: ignore
        client.dispatcher.denomination.register_callback(denomination_callback)  # type: ignore
        client.dispatcher.sale.register_callback(wsm_sale_callback)  # type: ignore
        client.dispatcher.payment_card_get.register_callback(
            wsm_payment_card_get_callback,  # type: ignore
        )
        client.dispatcher.encashment.register_callback(wsm_encashment_callback)  # type: ignore
        yield client
