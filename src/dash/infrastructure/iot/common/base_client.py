from typing import Any, Literal, Mapping

from npc_iot.base import BaseClient, BaseDispatcher, MessageHandler
from npc_iot.exception import DeviceResponceError

from dash.services.common.errors.controller import (
    ControllerResponseError,
    ControllerTimeoutError,
)


class BaseIoTDispatcher(BaseDispatcher):
    state_info = MessageHandler(topic="/+/server/state/info")
    state = MessageHandler(topic="/+/server/state", is_result=True)
    config = MessageHandler(topic="/+/server/config", is_result=True)
    setting = MessageHandler(topic="/+/server/setting", is_result=True)
    display = MessageHandler(topic="/+/server/display", is_result=True)
    denomination = MessageHandler(topic="/+/server/denomination/info")
    sale = MessageHandler(topic="/+/server/sale/set")
    payment_card_get = MessageHandler(topic="/+/server/payment/card/get")
    encashment = MessageHandler(topic="/+/server/incass/set")
    reboot_ack = MessageHandler(topic="/+/server/reboot/ack", is_ack=True)
    config_ack = MessageHandler(topic="/+/server/config/ack", is_ack=True)
    setting_ack = MessageHandler(topic="/+/server/setting/ack", is_ack=True)
    action_ack = MessageHandler(topic="/+/server/action/ack", is_ack=True)
    payment_ack = MessageHandler(topic="/+/server/payment/ack", is_ack=True)


class BaseIoTClient(BaseClient[BaseIoTDispatcher]):
    async def _wait_for_response(
        self,
        device_id: str,
        topic: str,
        qos: Literal[0, 1, 2],
        payload: Mapping[str, Any] | None,
        ttl: int | None,
        timeout: int = 2,
    ) -> dict[str, Any]:
        waiter = await self.send_message(device_id, topic, qos, payload, ttl)
        try:
            response = await waiter.wait(timeout=timeout)
        except DeviceResponceError:
            raise ControllerResponseError
        except TimeoutError:
            raise ControllerTimeoutError

        return response

    async def reboot(
        self,
        device_id: str,
        payload: dict[str, Any],
        ttl: int | None = 5,
    ) -> dict[str, Any]:
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/reboot/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

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
            timeout=5,
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
            timeout=5,
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
        await self.send_message(
            device_id=device_id,
            topic="client/payment/card",
            qos=1,
            payload=payload,
            ttl=None,
        )

    async def sale_ack(self, device_id: str, transaction_id: int) -> None:
        await self.send_message(
            device_id=device_id,
            topic="client/sale/ack",
            payload={"id": transaction_id, "code": 0},
            qos=1,
            ttl=None,
        )

    async def encashment_ack(self, device_id: str, payload: dict[str, Any]) -> None:
        await self.send_message(
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
