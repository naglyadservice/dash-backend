from enum import StrEnum
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base, TimestampMixin, UUIDMixin


class ControllerType(StrEnum):
    CARWASH = "CARWASH_CONTROLLER"
    WATER_VENDING = "WATER_VENDING_CONTROLLER"
    VACUUM = "VACUUM_CONTROLLER"


class ControllerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    NOT_ACTIVE = "NOT_ACTIVE"


class Controller(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "controllers"

    device_id: Mapped[str] = mapped_column(unique=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    type: Mapped[ControllerType] = mapped_column()
    name: Mapped[str | None] = mapped_column()
    version: Mapped[str] = mapped_column()
    status: Mapped[ControllerStatus]

    monopay_token: Mapped[str | None] = mapped_column()
    monopay_active: Mapped[bool] = mapped_column(default=False)
    liqpay_public_key: Mapped[str | None] = mapped_column()
    liqpay_private_key: Mapped[str | None] = mapped_column()
    liqpay_active: Mapped[bool] = mapped_column(default=False)

    state: Mapped[dict[str, Any] | None] = mapped_column()
    settings: Mapped[dict[str, Any] | None] = mapped_column()
    config: Mapped[dict[str, Any] | None] = mapped_column()

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "controller"}
