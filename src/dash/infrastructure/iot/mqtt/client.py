from typing import Any

from npc_iot.base import BaseClient, BaseDispatcher, MessageHandler


def tasmota_id_parser(topic_prefix: str, topic: str) -> str:
    return topic.split("/")[1]


def sys_client_id_parser(topic_prefix: str, topic: str) -> str:
    return topic.split("/")[4]


class MqttDispatcher(BaseDispatcher):
    tasmota_state = MessageHandler(
        topic="tele/+/SENSOR", device_id_parser=tasmota_id_parser
    )
    sys_disconnect = MessageHandler(
        topic="$SYS/brokers/+/clients/+/disconnected",
        device_id_parser=sys_client_id_parser,
    )
    sys_connect = MessageHandler(
        topic="$SYS/brokers/+/clients/+/connected",
        device_id_parser=sys_client_id_parser,
    )


class MqttClient(BaseClient[MqttDispatcher]):
    async def tasmota_power_on(self, device_id: str) -> None:
        await self.send_raw_message(
            topic=f"cmnd/{device_id}/POWER",
            payload="ON",
            qos=1,
            ttl=None,
        )

    async def tasmota_power_off(self, device_id: str) -> None:
        await self.send_raw_message(
            topic=f"cmnd/{device_id}/POWER",
            payload="OFF",
            qos=1,
            ttl=None,
        )
