from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.controllers.controller import Controller, ControllerType


class CarwashController(Controller):
    __tablename__ = "carwash_controllers"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )

    @property
    def tariff(self) -> dict[str, int]:
        return self.settings["tariff"]

    __mapper_args__ = {"polymorphic_identity": ControllerType.CARWASH.value}
