from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base


class PaymentStatus(StrEnum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    HOLD = "HOLD"
    COMPLETED = "COMPLETED"
    REVERSED = "REVERSED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class PaymentType(StrEnum):
    BILL = "BILL"
    COIN = "COIN"
    PAYPASS = "PAYPASS"
    MONOPAY = "MONOPAY"
    FREE = "FREE"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    invoice_id: Mapped[str | None] = mapped_column(unique=True)
    controller_id: Mapped[int] = mapped_column(ForeignKey("controllers.id"))
    amount: Mapped[int] = mapped_column()
    status: Mapped[PaymentStatus] = mapped_column()
    type: Mapped[PaymentType] = mapped_column()
    failure_reason: Mapped[str | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
