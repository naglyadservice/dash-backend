from datetime import datetime
from enum import StrEnum
from typing import Any
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
    CASH = "CASH"
    CASHLESS = "CASHLESS"
    FREE = "FREE"


class PaymentGatewayType(StrEnum):
    MONOPAY = "MONOPAY"
    LIQPAY = "LIQPAY"
    PAYPASS = "PAYPASS"


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    invoice_id: Mapped[str | None] = mapped_column(unique=True)
    controller_id: Mapped[UUID] = mapped_column(
        ForeignKey("controllers.id", ondelete="SET NULL")
    )
    location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL")
    )
    transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="SET NULL")
    )
    receipt_id: Mapped[UUID | None] = mapped_column()
    amount: Mapped[int] = mapped_column()
    status: Mapped[PaymentStatus] = mapped_column()
    type: Mapped[PaymentType] = mapped_column()
    gateway_type: Mapped[PaymentGatewayType | None] = mapped_column()
    failure_reason: Mapped[str | None] = mapped_column()
    checkbox_error: Mapped[str | None] = mapped_column()
    created_at_controller: Mapped[datetime | None] = mapped_column()
    extra: Mapped[dict[str, Any] | None] = mapped_column()

    @property
    def receipt_url(self) -> str | None:
        return f"https://check.checkbox.ua/{self.receipt_id}"
