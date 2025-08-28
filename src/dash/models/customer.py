from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base, TimestampMixin, UUIDMixin


class Customer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "customers"

    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str | None] = mapped_column()
    phone_number: Mapped[str] = mapped_column()
    password_hash: Mapped[str | None] = mapped_column()
    card_id: Mapped[str | None] = mapped_column()
    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), default=Decimal("0.00")
    )
    last_balance_update: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tariff_per_liter_1: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2, asdecimal=True)
    )
    tariff_per_liter_2: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2, asdecimal=True)
    )
    birth_date: Mapped[date | None] = mapped_column()
    discount_percent: Mapped[int | None] = mapped_column()

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "phone_number",
            name="uix_customer_company_phone_number",
        ),
        UniqueConstraint(
            "company_id",
            "card_id",
            name="uix_customer_company_card_id",
        ),
        CheckConstraint(
            "phone_number IS NOT NULL OR card_id IS NOT NULL",
            name="cc_customer_identity",
        ),
        Index("ix_customer_company_id", "company_id", "id"),
    )
