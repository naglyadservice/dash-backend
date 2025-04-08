from typing import Sequence

from sqlalchemy import delete, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.models.user import User, UserRole


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def exists(self, email: str) -> bool:
        stmt = select(exists().where(User.email == email))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists_by_id(self, user_id: int) -> bool:
        stmt = select(exists().where(User.id == user_id))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return await self.session.scalar(stmt)

    async def get_list(self, owner_id: int | None = None) -> Sequence[User]:
        stmt = select(User).options(
            selectinload(User.owned_locations),
            selectinload(User.administrated_locations),
        )
        if owner_id is not None:
            stmt = stmt.where(
                LocationAdmin.location_id.in_(
                    select(Location.id).where(Location.owner_id == owner_id)
                )
            )

        result = await self.session.scalars(stmt)
        return result.unique().all()

    async def is_location_owner(self, user_id: int, location_id: int) -> bool:
        stmt = select(
            exists().where(Location.id == location_id, Location.owner_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def is_location_admin(self, user_id: int, location_id: int) -> bool:
        stmt = select(
            exists().where(
                LocationAdmin.location_id == location_id,
                LocationAdmin.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_location_admin(self, user_id: int, location_id: int) -> None:
        stmt = delete(LocationAdmin).where(
            LocationAdmin.user_id == user_id, LocationAdmin.location_id == location_id
        )
        await self.session.execute(stmt)
