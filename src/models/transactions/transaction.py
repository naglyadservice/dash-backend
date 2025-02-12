from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class PaymentMethod(StrEnum):
    CASH = "CASH"
    MONOPAY = "MONOPAY"
    LIQPAY = "LIQPAY"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TransactionType(StrEnum):
    CARWASH = "CARWASH_TRANSACTION"
    WATER_VENDING = "WATER_VENDING_TRANSACTION"
    VACUUM = "VACUUM_TRANSACTION"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    controller_id: Mapped[str] = mapped_column(
        ForeignKey("controllers.id", ondelete="CASCADE")
    )
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE")
    )
    amount: Mapped[float] = mapped_column()
    payment_method: Mapped[PaymentMethod] = mapped_column()
    status: Mapped[PaymentStatus] = mapped_column()
    type: Mapped[TransactionType] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "transaction"}
