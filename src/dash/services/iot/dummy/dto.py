from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from dash.models.controllers.controller import ControllerStatus, ControllerType
from dash.services.iot.dto import IoTControllerBaseDTO


class DummyControllerIoTScheme(IoTControllerBaseDTO):
    type: Literal[ControllerType.DUMMY]
    description: str | None
    status: ControllerStatus
    
    @classmethod
    def get_state_dto(cls):
        pass

    model_config = ConfigDict(from_attributes=True)


class SetDummyDescriptionRequest(BaseModel):
    controller_id: UUID
    description: str | None
