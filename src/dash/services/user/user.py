import secrets

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.repositories.user import UserRepository
from dash.models.location_admin import LocationAdmin
from dash.models.user import User, UserRole
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.user import EmailAlreadyTakenError, UserNotFoundError
from dash.services.user.dto import (
    AddLocationAdminRequest,
    AddLocationAdminResponse,
    CreateUserRequest,
    CreateUserResponse,
    ReadUserListResponse,
    RemoveLocationAdminRequest,
    UserDTO,
)


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        identity_provider: IdProvider,
        password_processor: PasswordProcessor,
    ) -> None:
        self.user_repository = user_repository
        self.identity_provider = identity_provider
        self.password_processor = password_processor

    async def _create_user(
        self, data: CreateUserRequest, role: UserRole = UserRole.USER
    ) -> CreateUserResponse:
        if await self.user_repository.exists(data.email):
            raise EmailAlreadyTakenError

        password = secrets.token_urlsafe(16)

        user = User(
            name=data.name,
            email=data.email,
            role=role,
            password_hash=self.password_processor.hash(password),
        )
        self.user_repository.add(user)
        await self.user_repository.flush()

        return CreateUserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            password=password,
        )

    async def create_company_owner(self, data: CreateUserRequest) -> CreateUserResponse:
        return await self._create_user(data, role=UserRole.COMPANY_OWNER)

    async def add_location_admin(
        self, data: AddLocationAdminRequest
    ) -> AddLocationAdminResponse:
        await self.identity_provider.ensure_company_owner(data.location_id)

        new_user = None
        user_id = data.user_id

        if user_id is not None:
            if not await self.user_repository.exists_by_id(user_id):
                raise UserNotFoundError
        if data.user is not None:
            new_user = await self._create_user(data.user, role=UserRole.LOCATION_ADMIN)
            user_id = new_user.id

        admin = LocationAdmin(
            location_id=data.location_id,
            user_id=user_id,
        )
        self.user_repository.add(admin)
        await self.user_repository.commit()

        return AddLocationAdminResponse(user=new_user)

    async def remove_location_admin(self, data: RemoveLocationAdminRequest) -> None:
        await self.identity_provider.ensure_company_owner(data.location_id)

        if not await self.user_repository.is_location_admin(
            data.user_id, data.location_id
        ):
            raise UserNotFoundError

        await self.user_repository.delete_location_admin(data.user_id, data.location_id)
        await self.user_repository.commit()

    async def read_users(self) -> ReadUserListResponse:
        user = await self.identity_provider.authorize()

        if user.role is UserRole.SUPERADMIN:
            users = await self.user_repository.get_list()
        elif user.role is UserRole.COMPANY_OWNER:
            users = await self.user_repository.get_list(user.id)
        else:
            raise AccessForbiddenError

        return ReadUserListResponse(
            users=[UserDTO.model_validate(user, from_attributes=True) for user in users]
        )
