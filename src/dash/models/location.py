from enum import Enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base


class LocationType(str, Enum):
    CARWASH = "CARWASH"
    VENDING = "VENDING"


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE")
    )
    address: Mapped[str] = mapped_column()
    type: Mapped[LocationType] = mapped_column()
