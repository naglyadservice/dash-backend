from typing import Any, Literal, Mapping

from npc_iot import Dispatcher, NpcClient
from npc_iot.dispatcher import MessageHandler
from npc_iot.exception import DeviceResponceError

from dash.services.common.errors.controller import (
    ControllerResponseError,
    ControllerTimeoutError,
)


class BaseDispatcher(Dispatcher):
    def __init__(self, callback_kwargs: dict[str, Any] | None = None) -> None:
        super().__init__(callback_kwargs=callback_kwargs)

        self.config = MessageHandler(topic="/+/server/config", is_result=True)
        self.setting = MessageHandler(topic="/+/server/setting", is_result=True)
        self.denomination = MessageHandler(topic="/+/server/denomination/info")
        self.display = MessageHandler(topic="/+/server/display", is_result=True)
        self.action_ack = MessageHandler(topic="/+/server/action/ack", is_ack=True)
        self.payment_ack = MessageHandler(topic="/+/server/payment/ack", is_ack=True)
        self.sale = MessageHandler(topic="/+/server/sale/set")
        self.payment_card_get = MessageHandler(topic="/+/server/payment/card/get")
        self.encashment = MessageHandler(topic="/+/server/incass/set")


class BaseNpcClient(NpcClient[BaseDispatcher]):
    async def _wait_for_response(
        self,
        device_id: str,
        topic: str,
        qos: Literal[0, 1, 2],
        payload: Mapping[str, Any] | None,
        ttl: int | None,
    ) -> dict[str, Any]:
        waiter = await self._send_message(device_id, topic, qos, payload, ttl)
        try:
            response = await waiter.wait(timeout=1)
        except DeviceResponceError:
            raise ControllerResponseError
        except TimeoutError:
            raise ControllerTimeoutError

        return response

    async def set_config(
        self, device_id: str, payload: dict[str, Any], ttl: int | None = 5
    ) -> dict[str, Any]:
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/config/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

    async def get_config(
        self, device_id: str, fields: list | None = None, ttl: int | None = 5
    ) -> dict[str, Any]:
        if fields is None:
            fields = []

        return await self._wait_for_response(
            device_id=device_id,
            topic="client/config/get",
            qos=1,
            payload={"fields": fields},
            ttl=ttl,
        )

    async def set_settings(
        self, device_id: str, payload: dict[str, Any], ttl: int | None = 5
    ) -> dict[str, Any]:
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/setting/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

    async def get_settings(
        self, device_id: str, fields: list | None = None, ttl: int | None = 5
    ) -> dict[str, Any]:
        if fields is None:
            fields = []

        return await self._wait_for_response(
            device_id=device_id,
            topic="client/setting/get",
            qos=1,
            payload={"fields": fields},
            ttl=ttl,
        )

    async def get_display(
        self, device_id: str, fields: list | None = None, ttl: int | None = 5
    ) -> dict[str, Any]:
        if fields is None:
            fields = []

        return await self._wait_for_response(
            device_id=device_id,
            topic="client/display/get",
            qos=1,
            payload={"fields": fields},
            ttl=ttl,
        )

    async def set_payment(
        self, device_id: str, payload: dict[str, Any], ttl: int | None = 5
    ) -> dict[str, Any]:
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/payment/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

    async def set_action(
        self, device_id: str, payload: dict[str, Any], ttl: int | None = 5
    ) -> dict[str, Any]:
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/action/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

    async def payment_card_ack(self, device_id: str, payload: dict[str, Any]) -> None:
        await self._send_message(
            device_id=device_id,
            topic="client/payment/card",
            qos=1,
            payload=payload,
            ttl=None,
        )

    async def sale_ack(self, device_id: str, transaction_id: int) -> None:
        await self._send_message(
            device_id=device_id,
            topic="client/sale/ack",
            payload={"id": transaction_id, "code": 0},
            qos=1,
            ttl=None,
        )

    async def encashment_ack(self, device_id: str, payload: dict[str, Any]) -> None:
        await self._send_message(
            device_id=device_id,
            topic="client/incass/ack",
            payload=payload,
            qos=1,
            ttl=None,
        )

    async def get_state(
        self, device_id: str, fields: list | None = None, ttl: int | None = 5
    ) -> dict[str, Any]:
        if fields is None:
            fields = []

        return await self._wait_for_response(
            device_id=device_id,
            topic="client/state/get",
            payload={"fields": fields},
            qos=1,
            ttl=ttl,
        )
