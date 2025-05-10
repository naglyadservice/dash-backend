from enum import StrEnum
from typing import (
    TYPE_CHECKING,
    Any,
)
from uuid import UUID

from sqlalchemy import ForeignKey, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from dash.models.location import Location

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
    location_id: Mapped[UUID | None] = mapped_column(ForeignKey("locations.id"))
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

    location: Mapped["Location | None"] = relationship()

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "controller"}

    @hybrid_property
    def company_id(self) -> int | None:
        if self.location:
            return self.location.company_id
        return None

    @company_id.expression
    def company_id(self):
        # This expression allows you to use Controller.company_id in queries
        # It creates a subquery to get the company_id from the related location.
        # This requires that Location model is imported.
        # Ensure Location is imported for this expression to work (not just in TYPE_CHECKING)
        from dash.models.location import Location

        return (
            select(Location.company_id)
            .where(Location.id == self.location_id)
            .label("company_id")
        )
