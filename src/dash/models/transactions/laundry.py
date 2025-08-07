from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.payment import Payment
from dash.models.transactions.transaction import Transaction, TransactionType


class LaundrySessionStatus(StrEnum):
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    WAITING_START = "WAITING_START"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


class LaundryTransaction(Transaction):
    __tablename__ = "laundry_transactions"

    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id"), primary_key=True
    )
    payment_id: Mapped[UUID] = mapped_column(ForeignKey("payments.id"))
    tariff_type: Mapped[str] = mapped_column()
    session_status: Mapped[LaundrySessionStatus] = mapped_column()
    session_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hold_amount: Mapped[int | None] = mapped_column()
    refund_amount: Mapped[int | None] = mapped_column()
    final_amount: Mapped[int] = mapped_column()

    payment: Mapped[Payment] = relationship(lazy="joined")

    __mapper_args__ = {"polymorphic_identity": TransactionType.LAUNDRY.value}
