from typing import Sequence
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from dash.infrastructure.repositories.base import BaseRepository
from dash.models import Customer


class CustomerRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, company_id: UUID, customer_id: UUID) -> Customer | None:
        stmt = (
            select(Customer).where(Customer.id == customer_id),
            Customer.company_id == company_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_email(self, company_id: UUID, email: str) -> Customer | None:
        stmt = select(Customer).where(
            Customer.email == email,
            Customer.company_id == company_id,
        )
        return await self.session.scalar(stmt)

    async def get_by_cart(self, company_id: UUID, cart_id: str) -> Customer | None:
        stmt = select(Customer).where(
            Customer.cart_id == cart_id,
            Customer.company_id == company_id,
        )
        return await self.session.scalar(stmt)

    async def exists(self, company_id: UUID, email: str) -> bool:
        stmt = select(
            exists().where(
                Customer.email == email,
                Customer.company_id == company_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists_by_id(self, company_id: UUID, user_id: int) -> bool:
        stmt = select(
            exists().where(
                Customer.id == user_id,
                Customer.company_id == company_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_list(self, company_id: UUID) -> Sequence[Customer]:
        stmt = select(Customer).where(Customer.company_id == company_id)

        result = await self.session.scalars(stmt)
        return result.unique().all()
