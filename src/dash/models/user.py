from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.base import Base
from dash.models.location import Location


class UserRole(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    COMPANY_OWNER = "COMPANY_OWNER"
    COMPANY_ADMIN = "СOMPANY_ADMIN"
    LOCATION_OWNER = "LOCATION_OWNER"
    LOCATION_ADMIN = "LOCATION_ADMIN"
    USER = "USER"


class User(Base, AsyncAttrs):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    password_hash: Mapped[str] = mapped_column()
    role: Mapped[UserRole] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    owned_locations: Mapped[list["Location"]] = relationship(
        back_populates="owner",
        foreign_keys="Location.owner_id",
    )
    administrated_locations: Mapped[list["Location"]] = relationship(
        secondary="location_admins",
        primaryjoin="User.id == LocationAdmin.user_id",
        secondaryjoin="LocationAdmin.location_id == Location.id",
    )

    @property
    def locations(self) -> list[Location] | None:
        return (self.owned_locations or self.administrated_locations) or None
