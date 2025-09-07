from npc_iot.base import MessageHandler

from dash.infrastructure.iot.common.base_client import BaseIoTClient, BaseIoTDispatcher


class CarwashIoTDispatcher(BaseIoTDispatcher):
    card_set = MessageHandler(topic="/+/server/payment/card/ack", is_ack=True)


class CarwashIoTClient(BaseIoTClient):
    async def set_session(
        self, device_id: str, payload: dict[str, str], ttl: int = 5
    ) -> None:
        await self._wait_for_response(
            device_id=device_id,
            topic="client/payment/card/set",
            payload=payload,
            ttl=ttl,
            qos=1,
        )
