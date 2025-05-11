from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.controllers.controller import Controller, ControllerType


class WaterVendingController(Controller):
    __tablename__ = "water_vending_controllers"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )

    __mapper_args__ = {"polymorphic_identity": ControllerType.WATER_VENDING.value}
