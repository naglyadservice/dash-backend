from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.controllers.controller import Controller, ControllerType


class WaterVendingController(Controller):
    __tablename__ = "water_vending_controllers"

    controller_id: Mapped[int] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )
    display: Mapped[dict[str, Any] | None] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": ControllerType.WATER_VENDING.value}
