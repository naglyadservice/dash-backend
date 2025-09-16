import secrets

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.models.admin_user import AdminRole, AdminUser
from dash.models.location_admin import LocationAdmin
from dash.services.common.errors.base import AccessForbiddenError, ValidationError
from dash.services.common.errors.location import LocationNotFoundError
from dash.services.common.errors.user import EmailAlreadyTakenError, UserNotFoundError
from dash.services.user.dto import (
    AddLocationAdminRequest,
    AddLocationAdminResponse,
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserRequest,
    ReadUserListResponse,
    RegeneratePasswordRequest,
    RegeneratePasswordResponse,
    RemoveLocationAdminRequest,
    UpdateOwnerRequest,
    UserDTO,
)


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        location_repository: LocationRepository,
        identity_provider: IdProvider,
        password_processor: PasswordProcessor,
    ) -> None:
        self.user_repository = user_repository
        self.location_repository = location_repository
        self.identity_provider = identity_provider
        self.password_processor = password_processor

    async def _create_user(
        self, data: CreateUserRequest, role: AdminRole
    ) -> CreateUserResponse:
        if await self.user_repository.exists(data.email):
            raise EmailAlreadyTakenError

        password = secrets.token_urlsafe(8)

        user = AdminUser(
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
        return await self._create_user(data, role=AdminRole.COMPANY_OWNER)

    async def add_location_admin(
        self, data: AddLocationAdminRequest
    ) -> AddLocationAdminResponse:
        await self.identity_provider.ensure_company_owner(location_id=data.location_id)

        location = await self.location_repository.get(data.location_id)
        if not location:
            raise LocationNotFoundError

        new_user_dto = None
        user = None

        if data.user_id is not None:
            user = await self.user_repository.get(data.user_id)

        elif data.user is not None:
            new_user_dto = await self._create_user(
                data.user, role=AdminRole.LOCATION_ADMIN
            )
            user = await self.user_repository.get(new_user_dto.id)

        if user is None:
            raise UserNotFoundError

        admin = LocationAdmin(
            location_id=data.location_id,
            user_id=user.id,
        )
        user.company_id = location.company_id

        self.user_repository.add(admin)
        await self.user_repository.commit()

        return AddLocationAdminResponse(user=new_user_dto)

    async def remove_admin_from_location(
        self, data: RemoveLocationAdminRequest
    ) -> None:
        await self.identity_provider.ensure_company_owner(location_id=data.location_id)

        if not await self.user_repository.is_location_admin(
            data.user_id, data.location_id
        ):
            raise UserNotFoundError

        await self.user_repository.delete_location_admin(data.user_id, data.location_id)
        await self.user_repository.commit()

    async def delete_user(self, data: DeleteUserRequest) -> None:
        user = await self.user_repository.get(data.id)
        if not user:
            raise UserNotFoundError

        if user.role is AdminRole.COMPANY_OWNER:
            await self.identity_provider.ensure_superadmin()
        elif user.role is AdminRole.LOCATION_ADMIN:
            await self.identity_provider.ensure_company_owner(user.company_id)
        else:
            raise AccessForbiddenError

        await self.user_repository.delete_user(user)
        await self.user_repository.commit()

    async def read_users(self) -> ReadUserListResponse:
        user = await self.identity_provider.authorize()

        if user.role is AdminRole.SUPERADMIN:
            users = await self.user_repository.get_list()
        elif user.role is AdminRole.COMPANY_OWNER:
            users = await self.user_repository.get_list(user.id)
        else:
            raise AccessForbiddenError

        return ReadUserListResponse(
            users=[UserDTO.model_validate(user) for user in users]
        )

    async def regenerate_password(
        self, data: RegeneratePasswordRequest
    ) -> RegeneratePasswordResponse:
        await self.identity_provider.ensure_superadmin()

        user = await self.user_repository.get(data.id)
        if not user:
            raise UserNotFoundError

        password = secrets.token_urlsafe(8)

        user.password_hash = self.password_processor.hash(password)
        await self.user_repository.commit()

        return RegeneratePasswordResponse(new_password=password)

    async def update_owner(self, data: UpdateOwnerRequest) -> None:
        await self.identity_provider.ensure_superadmin()

        user = await self.user_repository.get(data.id)
        if not user:
            raise UserNotFoundError

        if user.role != AdminRole.COMPANY_OWNER:
            raise ValidationError("User is not COMPANY_OWNER")

        user.subscription_paid_until = data.subscription_paid_until
        user.subscription_payment_details = data.subscription_payment_details
        user.subscription_amount = data.subscription_amount
        user.is_blocked = data.is_blocked

        await self.user_repository.commit()
