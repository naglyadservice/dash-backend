from typing import AsyncIterator

from dishka import AsyncContainer

from dash.infrastructure.iot.common.base_client import BaseDispatcher, BaseNpcClient
from dash.main.config import MqttConfig
from dash.presentation.callbacks_wsm.denomination import denomination_callback
from dash.presentation.callbacks_wsm.encashment import encashment_callback
from dash.presentation.callbacks_wsm.payment_card_get import payment_card_get_callback
from dash.presentation.callbacks_wsm.sale import sale_callback
from dash.presentation.callbacks_wsm.state_info import state_info_callback


class WsmClient(BaseNpcClient):
    pass


async def get_wsm_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[WsmClient]:
    async with WsmClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="wsm",
        dispatcher=BaseDispatcher(callback_kwargs={"di_container": di_container}),
    ) as client:
        client.dispatcher.state_info.register_callback(state_info_callback)  # type: ignore
        client.dispatcher.sale.register_callback(sale_callback)  # type: ignore
        client.dispatcher.denomination.register_callback(denomination_callback)  # type: ignore
        client.dispatcher.payment_card_get.register_callback(payment_card_get_callback)  # type: ignore
        client.dispatcher.encashment.register_callback(encashment_callback)  # type: ignore
        yield client
