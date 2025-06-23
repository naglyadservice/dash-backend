from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .controller import Controller, ControllerType


class FiscalizerController(Controller):
    __tablename__ = "fiscalizer_controllers"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )

    __mapper_args__ = {"polymorphic_identity": ControllerType.FISCALIZER.value}
