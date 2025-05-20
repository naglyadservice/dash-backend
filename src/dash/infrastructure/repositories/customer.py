from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, exists, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models import Customer
from dash.models.company import Company
from dash.services.customer.dto import ReadCustomerListRequest


class CustomerRepository(BaseRepository):
    async def get(self, customer_id: UUID) -> Customer | None:
        stmt = select(Customer).where(Customer.id == customer_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_email(self, company_id: UUID, email: str) -> Customer | None:
        stmt = select(Customer).where(
            Customer.email == email,
            Customer.company_id == company_id,
        )
        return await self.session.scalar(stmt)

    async def get_by_card_id(self, company_id: UUID, card_id: str) -> Customer | None:
        stmt = select(Customer).where(
            Customer.card_id == card_id,
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

    async def exists_by_id(self, company_id: UUID, user_id: UUID) -> bool:
        stmt = select(
            exists().where(
                Customer.id == user_id,
                Customer.company_id == company_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists_by_card_id(self, company_id: UUID, card_id: str) -> bool:
        stmt = select(
            exists().where(
                Customer.card_id == card_id,
                Customer.company_id == company_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete(self, customer: Customer) -> None:
        await self.session.delete(customer)

    async def _get_list(
        self,
        data: ReadCustomerListRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> tuple[Sequence[Customer], int]:
        stmt = select(Customer)

        if data.company_id is not None:
            stmt = stmt.where(Customer.company_id == data.company_id)

        elif whereclause is not None:
            stmt = stmt.where(whereclause)
        paginated_stmt = (
            stmt.order_by(Customer.created_at.desc())
            .offset(data.offset)
            .limit(data.limit)
        )

        paginated = (await self.session.scalars(paginated_stmt)).unique().all()
        total = await self._get_count(stmt)

        return paginated, total

    async def get_list_all(
        self, data: ReadCustomerListRequest
    ) -> tuple[Sequence[Customer], int]:
        return await self._get_list(data)

    async def get_list_by_owner(
        self, data: ReadCustomerListRequest, user_id: UUID
    ) -> tuple[Sequence[Customer], int]:
        whereclause = Customer.company_id.in_(
            select(Company.id).where(Company.owner_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def get_list_by_admin(
        self, data: ReadCustomerListRequest, company_id: UUID
    ) -> tuple[Sequence[Customer], int]:
        whereclause = Customer.company_id == company_id
        return await self._get_list(data, whereclause)
