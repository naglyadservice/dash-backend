from npc_iot.base.client import BaseClient
from npc_iot.base.dispatcher import BaseDispatcher, MessageHandler


def tasmota_id_parser(topic_prefix: str, topic: str) -> str:
    return topic.split("/")[2]


class MqttDispatcher(BaseDispatcher):
    tasmota_state = MessageHandler(
        topic="/tele/+/SENSOR", device_id_parser=tasmota_id_parser
    )


class MqttClient(BaseClient[MqttDispatcher]):
    async def power_on(self, device_id: str) -> None:
        await self.send_message(
            device_id=device_id,
            topic=f"cmnd/{device_id}/POWER",
            payload="ON",
            qos=0,
            ttl=None,
        )

    async def power_off(self, device_id: str) -> None:
        await self.send_message(
            device_id=device_id,
            topic=f"cmnd/{device_id}/POWER",
            payload="OFF",
            qos=0,
            ttl=None,
        )
