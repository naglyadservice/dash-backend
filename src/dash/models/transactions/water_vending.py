from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.transactions.transaction import Transaction, TransactionType


class WaterVendingTransaction(Transaction):
    __tablename__ = "water_vending_transactions"

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), primary_key=True
    )
    out_liters_1: Mapped[int] = mapped_column()
    out_liters_2: Mapped[int] = mapped_column()

    sale_type: Mapped[str] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": TransactionType.WATER_VENDING.value}
