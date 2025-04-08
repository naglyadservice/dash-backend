from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.base import Base

if TYPE_CHECKING:
    from dash.models.user import User


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column()
    address: Mapped[str | None] = mapped_column()

    owner: Mapped["User"] = relationship(
        lazy="joined", back_populates="owned_locations"
    )
