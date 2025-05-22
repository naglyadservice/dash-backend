from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dash.models.base import Base, CreatedAtMixin, UUIDMixin
from dash.models.customer import Customer


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
    location_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL")
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL")
    )
    coin_amount: Mapped[int] = mapped_column()
    bill_amount: Mapped[int] = mapped_column()
    prev_amount: Mapped[int] = mapped_column()
    free_amount: Mapped[int] = mapped_column()
    qr_amount: Mapped[int] = mapped_column()
    paypass_amount: Mapped[int] = mapped_column()
    type: Mapped[TransactionType] = mapped_column()
    created_at_controller: Mapped[datetime] = mapped_column()
    sale_type: Mapped[str] = mapped_column()
    card_balance_in: Mapped[int | None] = mapped_column()
    card_balance_out: Mapped[int | None] = mapped_column()
    card_uid: Mapped[str | None] = mapped_column()

    customer: Mapped["Customer"] = relationship(lazy="joined")

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "transaction"}

    __table_args__ = (
        UniqueConstraint(
            controller_transaction_id,
            controller_id,
            created_at_controller,
            name="uix_transaction_controller_transaction_id",
        ),
    )
