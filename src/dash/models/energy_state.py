from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base, CreatedAtMixin, UUIDMixin


class DailyEnergyState(Base, UUIDMixin, CreatedAtMixin):
    __tablename__ = "daily_energy_states"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id", ondelete="CASCADE")
    )
    energy: Mapped[float] = mapped_column()
    date: Mapped["date"] = mapped_column(Date)
