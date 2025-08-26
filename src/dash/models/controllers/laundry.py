from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.controllers.controller import Controller, ControllerType


class LaundryTariffType(StrEnum):
    FIXED = "FIXED"
    PER_MINUTE = "PER_MINUTE"


class LaundryStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    PROCESSING = "PROCESSING"


class LaundryController(Controller):
    __tablename__ = "laundry_controllers"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )
    input_id: Mapped[int] = mapped_column(default=1)
    tariff_type: Mapped[LaundryTariffType] = mapped_column(
        default=LaundryTariffType.FIXED
    )
    laundry_status: Mapped[LaundryStatus] = mapped_column(
        default=LaundryStatus.AVAILABLE
    )
    timeout_minutes: Mapped[int] = mapped_column(default=5)

    fixed_price: Mapped[int] = mapped_column(default=1000)
    max_hold_amount: Mapped[int] = mapped_column(default=1000)
    price_per_minute_before_transition: Mapped[int] = mapped_column(default=100)
    transition_after_minutes: Mapped[int] = mapped_column(default=30)
    price_per_minute_after_transition: Mapped[int] = mapped_column(default=100)

    __mapper_args__ = {"polymorphic_identity": ControllerType.LAUNDRY.value}
