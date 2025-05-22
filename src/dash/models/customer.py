from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (CheckConstraint, ForeignKey, Index, Numeric,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base, TimestampMixin, UUIDMixin


class Customer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "customers"

    company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"))
    email: Mapped[str | None] = mapped_column(index=True)
    name: Mapped[str | None] = mapped_column()
    password_hash: Mapped[str | None] = mapped_column()
    card_id: Mapped[str | None] = mapped_column()
    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), default=Decimal("0.00")
    )
    tariff_per_liter_1: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2, asdecimal=True)
    )
    tariff_per_liter_2: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2, asdecimal=True)
    )
    birth_date: Mapped[date | None] = mapped_column()
    phone_number: Mapped[str | None] = mapped_column()
    discount_percent: Mapped[int | None] = mapped_column()

    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "email",
            name="uix_customer_company_email",
        ),
        UniqueConstraint(
            "company_id",
            "card_id",
            name="uix_customer_company_card_id",
        ),
        CheckConstraint(
            "email IS NOT NULL OR card_id IS NOT NULL", name="cc_customer_identity"
        ),
        Index("ix_customer_company_id", "company_id", "id"),
    )
