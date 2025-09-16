from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.controllers.controller import Controller, ControllerType


class DummyController(Controller):
    __tablename__ = "dummy_controllers"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )
    description: Mapped[str | None] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": ControllerType.DUMMY.value}
