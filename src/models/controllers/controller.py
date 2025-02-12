from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class ControllerType(StrEnum):
    CARWASH = "CARWASH_CONTROLLER"
    WATER_VENDING = "WATER_VENDING_CONTROLLER"
    VACUUM = "VACUUM_CONTROLLER"


class ControllerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    NOT_ACTIVE = "NOT_ACTIVE"


class Controller(Base):
    __tablename__ = "controllers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    serial_number: Mapped[str] = mapped_column()
    type: Mapped[ControllerType] = mapped_column()
    name: Mapped[str | None] = mapped_column()
    version: Mapped[str] = mapped_column()
    status: Mapped[ControllerStatus]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "controller"}
