from typing import Any

from npc_iot import NpcClient
from npc_iot.dispatcher import Dispatcher, MessageHandler


class TasmotaDispatcher(Dispatcher):
    def __init__(self, callback_kwargs: dict[str, Any] | None = None) -> None:
        super().__init__(callback_kwargs=callback_kwargs)

        self.state = MessageHandler(topic="/+/SENSOR")


class TasmotaClient(NpcClient[Dispatcher]):
    pass
