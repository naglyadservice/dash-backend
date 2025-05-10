from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base, CreatedAtMixin, UUIDMixin


class TransactionType(StrEnum):
    CARWASH = "CARWASH_TRANSACTION"
    WATER_VENDING = "WATER_VENDING_TRANSACTION"
    VACUUM = "VACUUM_TRANSACTION"


class Transaction(Base, UUIDMixin, CreatedAtMixin):
    __tablename__ = "transactions"

    controller_transaction_id: Mapped[int] = mapped_column()
    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id", ondelete="SET NULL")
    )
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL")
    )
    coin_amount: Mapped[int] = mapped_column()
    bill_amount: Mapped[int] = mapped_column()
    prev_amount: Mapped[int] = mapped_column()
    free_amount: Mapped[int] = mapped_column()
    qr_amount: Mapped[int] = mapped_column()
    paypass_amount: Mapped[int] = mapped_column()
    type: Mapped[TransactionType] = mapped_column()
    created_at_controller: Mapped[datetime] = mapped_column()

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "transaction"}
