from typing import Any, AsyncIterator

from dishka import AsyncContainer
from npc_iot import Dispatcher as _Dispatcher
from npc_iot import NpcClient as _NpcClient
from npc_iot.dispatcher import MessageHandler
from npc_iot.response import ResponseWaiter

from dash.main.config import MqttConfig

from .callbacks.denomination import denomination_callback
from .callbacks.sale import sale_callback
from .callbacks.state_info import state_info_callback


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
    async def set_config(
        self, device_id: str, payload: dict[str, Any], ttl: int | None = 5
    ) -> ResponseWaiter[dict[str, Any]]:
        return await self._send_message(
            device_id=device_id,
            topic="client/config/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

    async def get_config(
        self, device_id: str, fields: list | None = None, ttl: int | None = 5
    ) -> ResponseWaiter[dict[str, Any]]:
        if fields is None:
            fields = []

        return await self._send_message(
            device_id=device_id,
            topic="client/config/get",
            qos=1,
            payload={"fields": fields},
            ttl=ttl,
        )

    async def set_settings(
        self, device_id: str, payload: dict[str, Any], ttl: int | None = 5
    ) -> ResponseWaiter[dict[str, Any]]:
        return await self._send_message(
            device_id=device_id,
            topic="client/setting/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

    async def get_settings(
        self, device_id: str, fields: list | None = None, ttl: int | None = 5
    ) -> ResponseWaiter[dict[str, Any]]:
        if fields is None:
            fields = []

        return await self._send_message(
            device_id=device_id,
            topic="client/setting/get",
            qos=1,
            payload={"fields": fields},
            ttl=ttl,
        )

    async def get_display(
        self, device_id: str, fields: list | None = None, ttl: int | None = 5
    ) -> ResponseWaiter[dict[str, Any]]:
        if fields is None:
            fields = []

        return await self._send_message(
            device_id=device_id,
            topic="client/display/get",
            qos=1,
            payload={"fields": fields},
            ttl=ttl,
        )
        # return {
        #     k: v for k, v in display.items() if v and v != " " and k != "request_id"
        # }

    async def set_payment(
        self, device_id: str, payload: dict[str, Any], ttl: int | None = 5
    ) -> ResponseWaiter[dict[str, Any]]:
        return await self._send_message(
            device_id=device_id,
            topic="client/payment/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

    async def set_action(
        self, device_id: str, payload: dict[str, Any], ttl: int | None = 5
    ) -> ResponseWaiter[dict[str, Any]]:
        return await self._send_message(
            device_id=device_id,
            topic="client/action/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )


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
        client.dispatcher.state_info.register_callback(state_info_callback)
        client.dispatcher.sale.register_callback(sale_callback)  # type: ignore
        client.dispatcher.denomination.register_callback(denomination_callback)  # type: ignore
        yield client
