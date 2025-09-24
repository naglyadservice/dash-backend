from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base, TimestampMixin, UUIDMixin


class Encashment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "encashments"

    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id", ondelete="CASCADE")
    )
    coin_1: Mapped[int] = mapped_column()
    coin_2: Mapped[int] = mapped_column()
    coin_3: Mapped[int] = mapped_column()
    coin_4: Mapped[int] = mapped_column()
    coin_5: Mapped[int] = mapped_column()
    coin_6: Mapped[int] = mapped_column()
    bill_1: Mapped[int] = mapped_column()
    bill_2: Mapped[int] = mapped_column()
    bill_3: Mapped[int] = mapped_column()
    bill_4: Mapped[int] = mapped_column()
    bill_5: Mapped[int] = mapped_column()
    bill_6: Mapped[int] = mapped_column()
    bill_7: Mapped[int] = mapped_column()
    bill_8: Mapped[int] = mapped_column()
    encashed_amount: Mapped[int] = mapped_column()
    received_amount: Mapped[int | None] = mapped_column()
    is_closed: Mapped[bool] = mapped_column(default=False)
    created_at_controller: Mapped[datetime] = mapped_column()
    controller_encashment_id: Mapped[int | None] = mapped_column()

    __table_args__ = (
        UniqueConstraint(
            controller_encashment_id,
            controller_id,
            created_at_controller,
            name="uix_encashment_controller_encashment_id",
        ),
    )
