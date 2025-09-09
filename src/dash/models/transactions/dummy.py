from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.transactions.transaction import Transaction, TransactionType


class DummyTransaction(Transaction):
    __tablename__ = "dummy_transactions"

    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id"), primary_key=True
    )

    __mapper_args__ = {"polymorphic_identity": TransactionType.DUMMY.value}
