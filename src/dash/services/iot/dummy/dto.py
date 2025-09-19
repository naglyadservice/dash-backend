from typing import Literal

from pydantic import ConfigDict

from dash.models.controllers.controller import ControllerStatus, ControllerType
from dash.services.common.dto import ControllerID
from dash.services.iot.dto import AmountDTO, IoTControllerBaseDTO


class DummyControllerIoTScheme(IoTControllerBaseDTO):
    type: Literal[ControllerType.DUMMY]
    description: str | None
    status: ControllerStatus

    @classmethod
    def get_state_dto(cls):
        pass

    model_config = ConfigDict(from_attributes=True)


class SetDummyDescriptionRequest(ControllerID):
    description: str


class AddCashPaymentRequest(ControllerID, AmountDTO):
    pass
