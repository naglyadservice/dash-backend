from fastapi import Request

from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.storages.session import SessionStorage
from dash.models.user import User


class AuthenticationError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


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

    async def get_current_user_id(self) -> int:
        user_id = await self.session_storage.get(self.session_id)
        if not user_id:
            raise AuthenticationError

        return user_id

    async def get_current_user(self) -> User:
        user_id = await self.get_current_user_id()
        user = await self.user_repository.get(user_id)
        if not user:
            raise UserNotFoundError

        return user
