from enum import Enum

from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.base import Base, TimestampMixin, UUIDMixin
from dash.models.company import Company
from dash.models.location import Location


class AdminRole(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    # MANUFACTURER_ADMIN = "MANUFACTURER_ADMIN"
    COMPANY_OWNER = "COMPANY_OWNER"
    # COMPANY_ADMINISTRATOR = "COMPANY_ADMINISTRATOR"
    LOCATION_ADMIN = "LOCATION_ADMIN"


class AdminUser(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "admin_users"

    email: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    password_hash: Mapped[str] = mapped_column()
    role: Mapped[AdminRole] = mapped_column()

    companies: Mapped[list["Company"]] = relationship(back_populates="owner")
    administrated_locations: Mapped[list["Location"]] = relationship(
        secondary="location_admins",
        primaryjoin="AdminUser.id == LocationAdmin.user_id",
        secondaryjoin="LocationAdmin.location_id == Location.id",
        viewonly=True,
    )
    owned_locations: Mapped[list["Location"]] = relationship(
        secondary="companies",
        primaryjoin="AdminUser.id == Company.owner_id",
        secondaryjoin="Company.id == Location.company_id",
        viewonly=True,
    )

    @property
    def locations(self) -> list[Location] | None:
        return (self.owned_locations or self.administrated_locations) or None
