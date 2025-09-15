from npc_iot.base import MessageHandler

from dash.infrastructure.iot.common.base_client import BaseIoTClient, BaseIoTDispatcher


class CarCleanerIoTDispatcher(BaseIoTDispatcher):
    card_set_ack = MessageHandler(topic="/+/server/payment/card/ack", is_ack=True)


class CarCleanerIoTClient(BaseIoTClient):
    pass
