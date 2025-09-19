from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from dash.models.company import Company


class Location(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "locations"

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column()
    address: Mapped[str | None] = mapped_column()

    company: Mapped["Company"] = relationship(back_populates="locations", lazy="joined")
