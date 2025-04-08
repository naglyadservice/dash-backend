from typing import Any, AsyncIterator

from dishka import AsyncContainer
from npc_iot import Dispatcher as _Dispatcher
from npc_iot import NpcClient as _NpcClient
from npc_iot.dispatcher import MessageHandler

from dash.infrastructure.mqtt.callbacks.denomination import denomination_callback
from dash.infrastructure.mqtt.callbacks.sale import sale_callback
from dash.infrastructure.mqtt.callbacks.state_info import state_info_callback
from dash.main.config import MqttConfig


class Dispatcher(_Dispatcher):
    def __init__(self, callback_kwargs: dict[str, Any] | None = None) -> None:
        super().__init__(callback_kwargs=callback_kwargs)

        self.config = MessageHandler(topic="/+/server/config", is_result=True)
        self.setting = MessageHandler(topic="/+/server/setting", is_result=True)
        self.denomination = MessageHandler(topic="/+/server/denomination/info")
        self.display = MessageHandler(topic="/+/server/display", is_result=True)
        self.action_ack = MessageHandler(topic="/+/server/action/ack", is_ack=True)
        self.payment_ack = MessageHandler(topic="/+/server/payment/ack", is_ack=True)
        self.sale = MessageHandler(topic="/+/server/sale/set")


class NpcClient(_NpcClient[Dispatcher]):
    pass


async def get_npc_client(
    config: MqttConfig, di_container: AsyncContainer
) -> AsyncIterator[NpcClient]:
    async with NpcClient(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        topic_prefix="wsm",
        dispatcher=Dispatcher(callback_kwargs={"di_container": di_container}),
    ) as client:
        # client.dispatcher.state_info.register_callback(state_info_callback)
        # client.dispatcher.sale.register_callback(sale_callback)  # type: ignore
        # client.dispatcher.denomination.register_callback(denomination_callback)  # type: ignore
        yield client
