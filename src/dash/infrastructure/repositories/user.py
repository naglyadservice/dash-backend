from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.admin_user import AdminUser
from dash.models.company import Company
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> AdminUser | None:
        return await self.session.get(AdminUser, user_id)

    async def exists(self, email: str) -> bool:
        stmt = select(exists().where(AdminUser.email == email))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists_by_id(self, user_id: UUID) -> bool:
        stmt = select(exists().where(AdminUser.id == user_id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_email(self, email: str) -> AdminUser | None:
        stmt = select(AdminUser).where(AdminUser.email == email)
        return await self.session.scalar(stmt)

    async def get_list(self, owner_id: UUID | None = None) -> Sequence[AdminUser]:
        stmt = select(AdminUser).options(
            selectinload(AdminUser.owned_locations),
            selectinload(AdminUser.administrated_locations),
        )
        if owner_id is not None:
            stmt = stmt.where(
                LocationAdmin.location_id.in_(
                    select(Location.id)
                    .join(Company)
                    .where(Company.owner_id == owner_id)
                )
            )

        result = await self.session.scalars(stmt)
        return result.unique().all()

    async def is_company_owner(self, user_id: UUID, location_id: UUID) -> bool:
        stmt = select(
            exists().where(
                Location.id == location_id,
                Location.company_id == Company.id,
                Company.owner_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def is_location_admin(self, user_id: UUID, location_id: UUID) -> bool:
        stmt = select(
            exists().where(
                LocationAdmin.location_id == location_id,
                LocationAdmin.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_location_admin(self, user_id: UUID, location_id: UUID) -> None:
        stmt = delete(LocationAdmin).where(
            LocationAdmin.user_id == user_id, LocationAdmin.location_id == location_id
        )
        await self.session.execute(stmt)

    async def delete_user(self, user: AdminUser) -> None:
        await self.session.delete(user)
