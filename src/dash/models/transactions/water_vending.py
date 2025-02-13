from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.service_enum import WaterVendingServiceType
from dash.models.transactions.transaction import Transaction, TransactionType


class WaterVendingTransaction(Transaction):
    __tablename__ = "water_vending_transactions"

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), primary_key=True
    )
    service_type: Mapped[WaterVendingServiceType] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": TransactionType.WATER_VENDING.value}
