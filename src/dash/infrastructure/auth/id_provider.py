from uuid import UUID

from fastapi import Request

from dash.infrastructure.auth.errors import JWTTokenError, UserNotFoundError
from dash.infrastructure.auth.token_processor import JWTTokenProcessor
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.storages.session import SessionStorage
from dash.models.admin_user import AdminRole, AdminUser
from dash.services.common.errors.base import AccessDeniedError, AccessForbiddenError


class IdProvider:
    def __init__(
        self,
        request: Request,
        session_storage: SessionStorage,
        user_repository: UserRepository,
        token_processor: JWTTokenProcessor,
    ) -> None:
        self.jwt_token = self._fetch_token(request)
        self.session_storage = session_storage
        self.user_repository = user_repository
        self.token_processor = token_processor

        self._user: AdminUser

    def _fetch_token(self, request: Request) -> str:
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise JWTTokenError("Authorization header is missing")

        token = authorization.lstrip("Bearer").strip()
        if not token:
            raise JWTTokenError("Token is missing")

        return token

    async def authorize(self) -> AdminUser:
        if hasattr(self, "_user"):
            return self._user

        if await self.session_storage.is_blacklisted(self.jwt_token):
            raise JWTTokenError("Token has been revoked")

        user_id = self.token_processor.validate_access_token(self.jwt_token)
        user = await self.user_repository.get(user_id)
        if not user:
            raise UserNotFoundError

        self._user = user
        return user

    async def ensure_superadmin(self) -> None:
        await self.authorize()
        if self._user.role is not AdminRole.SUPERADMIN:
            raise AccessForbiddenError

    async def ensure_company_owner(
        self, company_id: UUID | None = None, location_id: UUID | None = None
    ) -> None:
        await self.authorize()
        if self._user.role is AdminRole.SUPERADMIN:
            return

        if not company_id and not location_id:
            raise AccessForbiddenError

        if self._user.role is AdminRole.COMPANY_OWNER:
            if company_id is not None:
                if not await self.user_repository.is_company_owner(
                    self._user.id, company_id
                ):
                    raise AccessForbiddenError
            elif location_id is not None:
                if not await self.user_repository.is_company_owner_by_location_id(
                    self._user.id, location_id
                ):
                    raise AccessForbiddenError
            return

        if self._user.role is AdminRole.LOCATION_ADMIN:
            raise AccessDeniedError

        raise AccessForbiddenError

    async def ensure_location_admin(self, location_id: UUID | None) -> None:
        await self.authorize()
        if self._user.role is AdminRole.SUPERADMIN:
            return

        if not location_id:
            raise AccessForbiddenError

        if self._user.role is AdminRole.COMPANY_OWNER:
            if not await self.user_repository.is_company_owner_by_location_id(
                self._user.id, location_id
            ):
                raise AccessForbiddenError
            return

        if self._user.role is AdminRole.LOCATION_ADMIN:
            if not await self.user_repository.is_location_admin(
                self._user.id, location_id
            ):
                raise AccessForbiddenError
            return

        raise AccessForbiddenError
