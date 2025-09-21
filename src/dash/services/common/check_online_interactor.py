from datetime import UTC, datetime, timedelta

from dash.infrastructure.storages.iot import IoTStorage
from dash.models.controllers.controller import Controller, ControllerType


class CheckOnlineInteractor:
    def __init__(self, iot_storage: IoTStorage):
        self.iot_storage = iot_storage

    async def __call__(self, controller: Controller) -> bool:
        if controller.type == ControllerType.DUMMY:
            return True

        state = await self.iot_storage.get_state(controller.id)

        if state and datetime.fromisoformat(state["created"]) + timedelta(
            minutes=3
        ) < datetime.now(UTC):
            return False

        return await self.iot_storage.is_online(controller.device_id)
