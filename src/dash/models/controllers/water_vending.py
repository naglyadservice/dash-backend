from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.controllers.controller import Controller, ControllerType


class WaterVendingController(Controller):
    __tablename__ = "water_vending_controllers"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )

    @property
    def tariff(self) -> dict[str, int]:
        return {
            "tariffPerLiter_1": self.settings["tariffPerLiter_1"],
            "tariffPerLiter_2": self.settings["tariffPerLiter_2"],
        }

    __mapper_args__ = {"polymorphic_identity": ControllerType.WATER_VENDING.value}
