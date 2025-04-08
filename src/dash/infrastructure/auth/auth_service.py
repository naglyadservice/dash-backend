import secrets
from dataclasses import dataclass

from pydantic import EmailStr

from dash.infrastructure.auth.errors import InvalidCredentialsError
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.storages.session import SessionStorage
from dash.models.user import User, UserRole
from dash.services.common.errors.user import EmailAlreadyTakenError


@dataclass
class RegisterUserRequest:
    email: EmailStr
    name: str
    password: str


@dataclass
class RegisterUserResponse:
    id: int


@dataclass
class LoginRequest:
    email: EmailStr
    password: str


@dataclass
class UserScheme:
    id: int
    email: str
    name: str
    role: UserRole


@dataclass
class LoginResponse:
    user: UserScheme
    session_id: str


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_processor: PasswordProcessor,
        session_storage: SessionStorage,
    ) -> None:
        self.user_repository = user_repository
        self.password_processor = password_processor
        self.session_storage = session_storage

    async def register(self, data: RegisterUserRequest) -> RegisterUserResponse:
        if await self.user_repository.exists(data.email):
            raise EmailAlreadyTakenError

        user = User(
            email=data.email,
            name=data.name,
            password_hash=self.password_processor.hash(data.password),
            role=UserRole.USER,
        )
        self.user_repository.add(user)
        await self.user_repository.commit()

        return RegisterUserResponse(id=user.id)

    async def authenticate(
        self, data: LoginRequest, session_id: str | None
    ) -> LoginResponse:
        if session_id:
            await self.session_storage.delete(session_id)

        user = await self.user_repository.get_by_email(data.email)
        if not user:
            raise InvalidCredentialsError

        if not self.password_processor.verify(data.password, user.password_hash):
            raise InvalidCredentialsError

        new_session_id = secrets.token_urlsafe(32)
        await self.session_storage.add(session_id=new_session_id, user_id=user.id)

        user_scheme = UserScheme(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
        )
        return LoginResponse(user=user_scheme, session_id=new_session_id)

    async def logout(self, session_id: str | None) -> None:
        if session_id:
            await self.session_storage.delete(session_id)
