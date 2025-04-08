from fastapi import Request

from dash.infrastructure.auth.errors import InvalidAuthSessionError, UserNotFoundError
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.storages.session import SessionStorage
from dash.models.user import User, UserRole
from dash.services.common.errors.base import AccessDeniedError, AccessForbiddenError


class IdProvider:
    def __init__(
        self,
        request: Request,
        session_storage: SessionStorage,
        user_repository: UserRepository,
    ) -> None:
        self.session_id: str | None = request.cookies.get("session")
        self.session_storage = session_storage
        self.user_repository = user_repository

        self._user_id = None
        self._user = None

    async def get_current_user_id(self) -> int:
        if self._user_id:
            return self._user_id

        user_id = await self.session_storage.get(self.session_id)
        if not user_id:
            raise InvalidAuthSessionError

        self._user_id = user_id
        return user_id

    async def get_current_user(self) -> User:
        if self._user:
            return self._user

        user_id = await self.get_current_user_id()
        user = await self.user_repository.get(user_id)
        if not user:
            raise UserNotFoundError

        self._user = user
        return user

    async def ensure_superadmin(self) -> None:
        user = await self.get_current_user()
        if user.role is not UserRole.SUPERADMIN:
            raise AccessForbiddenError

    async def ensure_location_owner(self, location_id: int | None) -> None:
        user = await self.get_current_user()
        if user.role is UserRole.SUPERADMIN:
            return

        if not location_id:
            raise AccessForbiddenError

        if user.role is UserRole.LOCATION_OWNER:
            if not await self.user_repository.is_location_owner(user.id, location_id):
                raise AccessForbiddenError
            return

        if user.role is UserRole.LOCATION_ADMIN:
            raise AccessDeniedError

        raise AccessForbiddenError

    async def ensure_location_admin(self, location_id: int | None) -> None:
        user = await self.get_current_user()
        if user.role is UserRole.SUPERADMIN:
            return

        if not location_id:
            raise AccessForbiddenError

        if user.role is UserRole.LOCATION_OWNER:
            if not await self.user_repository.is_location_owner(user.id, location_id):
                raise AccessForbiddenError
            return

        if user.role is UserRole.LOCATION_ADMIN:
            if not await self.user_repository.is_location_admin(user.id, location_id):
                raise AccessForbiddenError
            return

        raise AccessForbiddenError
