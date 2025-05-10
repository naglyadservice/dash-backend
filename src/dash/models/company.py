from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.base import Base
from dash.models.location import Location

if TYPE_CHECKING:
    from dash.models.admin_user import AdminUser


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column()

    locations: Mapped[list["Location"]] = relationship(back_populates="company")
    owner: Mapped["AdminUser"] = relationship(back_populates="companies", lazy="joined")
