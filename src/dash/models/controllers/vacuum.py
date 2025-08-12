from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.controllers.controller import Controller, ControllerType


class VacuumController(Controller):
    __tablename__ = "vacuum_controllers"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )

    @property
    def tariff(self) -> dict[str, int]:
        return self.settings["tariff"]

    @property
    def time_one_pay(self) -> int:
        return self.settings["timeOnePay"]

    @property
    def services_relay(self) -> list[int]:
        return self.settings["servicesRelay"]

    __mapper_args__ = {"polymorphic_identity": ControllerType.VACUUM.value}
