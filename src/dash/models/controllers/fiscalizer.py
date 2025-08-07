from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .controller import Controller, ControllerType


class FiscalizerController(Controller):
    __tablename__ = "fiscalizer_controllers"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )
    quick_deposit_button_1: Mapped[int | None] = mapped_column()
    quick_deposit_button_2: Mapped[int | None] = mapped_column()
    quick_deposit_button_3: Mapped[int | None] = mapped_column()
    sim_number: Mapped[str | None] = mapped_column()
    sim_serial: Mapped[str | None] = mapped_column()
    description: Mapped[str | None] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": ControllerType.FISCALIZER.value}
