from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.base import Base

if TYPE_CHECKING:
    from dash.models.company import Company


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column()
    address: Mapped[str | None] = mapped_column()

    company: Mapped["Company"] = relationship(back_populates="locations", lazy="joined")
