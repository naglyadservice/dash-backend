from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.base import Base, CreatedAtMixin, UUIDMixin
from dash.models.location import Location

if TYPE_CHECKING:
    from dash.models.admin_user import AdminUser


class Company(Base, UUIDMixin, CreatedAtMixin):
    __tablename__ = "companies"

    owner_id: Mapped[UUID] = mapped_column(ForeignKey("admin_users.id"))
    name: Mapped[str] = mapped_column()
    privacy_policy: Mapped[str | None] = mapped_column()
    offer_agreement: Mapped[str | None] = mapped_column()
    about: Mapped[str | None] = mapped_column()
    logo_key: Mapped[str | None] = mapped_column()

    locations: Mapped[list["Location"]] = relationship(back_populates="company")
    owner: Mapped["AdminUser"] = relationship(back_populates="companies", lazy="joined")
