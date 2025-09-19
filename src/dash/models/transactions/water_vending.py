from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.transactions.transaction import Transaction, TransactionType


class WsmTransaction(Transaction):
    __tablename__ = "water_vending_transactions"

    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True
    )
    out_liters_1: Mapped[int] = mapped_column()
    out_liters_2: Mapped[int] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": TransactionType.WATER_VENDING.value}
