from typing import Literal
from uuid import UUID

from pydantic import BaseModel

COIN_VALIDATOR_TYPE = Literal["protocol", "impulse"]


class ControllerID(BaseModel):
    controller_id: UUID
