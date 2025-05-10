from dash.infrastructure.auth.dto import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterUserRequest,
    RegisterUserResponse,
)
from dash.infrastructure.auth.errors import InvalidCredentialsError
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.auth.token_processor import JWTTokenProcessor
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.storages.session import SessionStorage
from dash.models.admin_user import AdminRole, AdminUser
from dash.services.common.errors.user import EmailAlreadyTakenError


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_processor: PasswordProcessor,
        session_storage: SessionStorage,
        token_processor: JWTTokenProcessor,
    ) -> None:
        self.user_repository = user_repository
        self.password_processor = password_processor
        self.session_storage = session_storage
        self.token_processor = token_processor

    async def register(self, data: RegisterUserRequest) -> RegisterUserResponse:
        if await self.user_repository.exists(data.email):
            raise EmailAlreadyTakenError

        user = AdminUser(
            email=data.email,
            name=data.name,
            password_hash=self.password_processor.hash(data.password),
            role=AdminRole.USER,
        )
        self.user_repository.add(user)
        await self.user_repository.commit()

        return RegisterUserResponse(
            access_token=self.token_processor.create_access_token(user.id),
            refresh_token=self.token_processor.create_refresh_token(user.id),
        )

    async def authenticate(self, data: LoginRequest) -> LoginResponse:
        user = await self.user_repository.get_by_email(data.email)
        if not user:
            raise InvalidCredentialsError

        if not self.password_processor.verify(data.password, user.password_hash):
            raise InvalidCredentialsError

        return LoginResponse(
            access_token=self.token_processor.create_access_token(user.id),
            refresh_token=self.token_processor.create_refresh_token(user.id),
        )

    async def refresh_token(self, data: RefreshTokenRequest) -> RefreshTokenResponse:
        user_id = self.token_processor.validate_refresh_token(data.refresh_token)
        return RefreshTokenResponse(
            access_token=self.token_processor.create_access_token(user_id),
        )

    async def logout(self, data: LogoutRequest) -> None:
        await self.session_storage.add_blacklist(data.access_token)
