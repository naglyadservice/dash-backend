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
        ttl: int = 5,
    ) -> dict[str, Any]:
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/state/set",
            qos=1,
            payload=payload,
            ttl=ttl,
        )

    async def get_state(self, device_id: str, ttl: int = 5) -> dict[str, Any]:
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/state/get",
            payload={"relay": [0, 1], "output": [0, 1, 2, 3, 4, 5], "input": [0, 1]},
            qos=1,
            ttl=ttl,
        )

    async def unlock_button_and_turn_on_led(
        self,
        device_id: str,
        duration_mins: int,
        relay_id: int,
        ouput_id: int,
        ttl: int = 10,
    ) -> dict[str, Any]:
        duration_ms = duration_mins * 60000
        return await self._wait_for_response(
            device_id=device_id,
            topic="client/state/set",
            payload={
                "relay": [{"id": relay_id, "state": True, "duration": duration_ms}],
                "output": [{"id": ouput_id, "state": True, "duration": duration_ms}],
            },
            qos=1,
            ttl=ttl,
        )

    async def lock_button_and_turn_off_led(
        self,
        device_id: str,
        relay_id: int,
        output_id: int,
    ) -> None:
        await self.send_message(
            device_id=device_id,
            topic="client/state/set",
            payload={
                "relay": [{"id": relay_id, "state": False}],
                "output": [{"id": output_id, "state": False}],
            },
            qos=1,
        )
