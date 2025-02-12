from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.models.service_enum import VacuumServiceType

from .transaction import Transaction, TransactionType


class VacuumTransaction(Transaction):
    __tablename__ = "vacuum_transactions"

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), primary_key=True
    )
    service_type: Mapped[VacuumServiceType] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": TransactionType.VACUUM.value}
