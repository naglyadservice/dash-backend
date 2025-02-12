from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.models.controllers.controller import Controller, ControllerType


class WaterVendingController(Controller):
    __tablename__ = "water_vending_controllers"

    controller_id: Mapped[int] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )

    __mapper_args__ = {"polymorphic_identity": ControllerType.WATER_VENDING.value}
