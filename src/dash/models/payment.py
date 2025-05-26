from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base, TimestampMixin, UUIDMixin


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
    LIQPAY = "LIQPAY"
    FREE = "FREE"


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    invoice_id: Mapped[str | None] = mapped_column(unique=True)
    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id", ondelete="SET NULL")
    )
    location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL")
    )
    receipt_id: Mapped[UUID | None] = mapped_column()
    amount: Mapped[int] = mapped_column()
    status: Mapped[PaymentStatus] = mapped_column()
    type: Mapped[PaymentType] = mapped_column()
    failure_reason: Mapped[str | None] = mapped_column()
    checkbox_error: Mapped[str | None] = mapped_column()
    created_at_controller: Mapped[datetime | None] = mapped_column()
