from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.service_enum import CarwashServiceType
from dash.models.transactions.transaction import Transaction, TransactionType


class CarwashTransaction(Transaction):
    __tablename__ = "carwash_transactions"

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), primary_key=True
    )
    service_type: Mapped[CarwashServiceType] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": TransactionType.CARWASH.value}
