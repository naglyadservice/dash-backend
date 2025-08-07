from typing import Any

from npc_iot.base import MessageHandler

from dash.infrastructure.iot.common.base_client import BaseIoTClient, BaseIoTDispatcher


class LaundryIoTDispatcher(BaseIoTDispatcher):
    state_ack = MessageHandler(topic="/+/server/state/ack", is_ack=True)


class LaundryIoTClient(BaseIoTClient):
    async def set_state(
        self,
        device_id: str,
        payload: dict[str, Any],
        ttl: int | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/state/set",
            qos=1,
            payload=payload,
            ttl=ttl,
            timeout=timeout,
        )

    async def unlock_button_and_turn_on_led(
        self, device_id: str, duration_mins: int, ttl: int = 10, timeout: int = 10
    ) -> dict[str, Any]:
        return await self.set_state(
            device_id=device_id,
            payload={
                "relay": [{"id": 1, "state": True}],
                "output": [{"id": 1, "state": True}],
                "duration": duration_mins * 60000,
            },
            ttl=ttl,
            timeout=timeout,
        )

    async def lock_button_and_turn_off_led(
        self, device_id: str, ttl: int | None = None, timeout: int = 10
    ) -> dict[str, Any]:
        return await self.set_state(
            device_id=device_id,
            payload={
                "relay": [{"id": 1, "state": False}],
                "output": [{"id": 1, "state": False}],
            },
            ttl=ttl,
            timeout=timeout,
        )
