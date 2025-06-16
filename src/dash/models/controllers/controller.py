from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models import Company

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
    name: Mapped[str] = mapped_column()
    version: Mapped[str] = mapped_column()
    status: Mapped[ControllerStatus]
    tasmota_id: Mapped[str | None] = mapped_column()

    monopay_token: Mapped[str | None] = mapped_column()
    monopay_active: Mapped[bool] = mapped_column(default=False)
    liqpay_public_key: Mapped[str | None] = mapped_column()
    liqpay_private_key: Mapped[str | None] = mapped_column()
    liqpay_active: Mapped[bool] = mapped_column(default=False)

    checkbox_login: Mapped[str | None] = mapped_column()
    checkbox_password: Mapped[str | None] = mapped_column()
    checkbox_active: Mapped[bool] = mapped_column(default=False)
    checkbox_license_key: Mapped[str | None] = mapped_column()
    good_name: Mapped[str | None] = mapped_column()
    good_code: Mapped[str | None] = mapped_column()
    tax_code: Mapped[str | None] = mapped_column()

    settings: Mapped[dict[str, Any]] = mapped_column()
    config: Mapped[dict[str, Any]] = mapped_column()

    location: Mapped["Location | None"] = relationship(lazy="joined")

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "controller"}

    @property
    def timezone(self) -> int:
        return self.config["timeZone"]

    @property
    def company(self) -> Company | None:
        return self.location and self.location.company

    @hybrid_property
    def company_id(self) -> UUID | None:
        return self.location and self.location.company_id

    @company_id.inplace.expression
    @classmethod
    def _company_id_expression(cls):
        from dash.models.location import Location

        return (
            select(Location.company_id)
            .where(Location.id == cls.location_id)
            .scalar_subquery()
        )
