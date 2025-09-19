from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.transactions.transaction import Transaction, TransactionType


class VacuumTransaction(Transaction):
    __tablename__ = "vacuum_transactions"

    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True
    )
    services_sold_seconds: Mapped[dict[str, Any]] = mapped_column()
    tariff: Mapped[dict[str, Any]] = mapped_column()
    replenishment_ratio: Mapped[int | None] = mapped_column()

    __mapper_args__ = {"polymorphic_identity": TransactionType.VACUUM.value}
