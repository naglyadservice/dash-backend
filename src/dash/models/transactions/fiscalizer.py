from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .transaction import Transaction, TransactionType


class FiscalizerTransaction(Transaction):
    __tablename__ = "fiscalizer_transactions"

    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id"), primary_key=True
    )

    __mapper_args__ = {"polymorphic_identity": TransactionType.FISCALIZER.value}
