from dataclasses import dataclass

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from dash.infrastructure.auth.auth_service import (
    AuthService,
    LoginRequest,
    LoginResponse,
    RegisterUserRequest,
    RegisterUserResponse,
)
from dash.infrastructure.auth.dto import (
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from dash.infrastructure.auth.id_provider import IdProvider
from dash.models.admin_user import AdminRole
from dash.presentation.bearer import bearer_scheme

auth_router = APIRouter(prefix="/auth", tags=["AUTH"], route_class=DishkaRoute)


@auth_router.post(
    "/register",
    status_code=201,
    responses={409: {"description": "Email already registered"}},
)
async def register(
    data: RegisterUserRequest, auth_service: FromDishka[AuthService]
) -> RegisterUserResponse:
    return await auth_service.register(data)


@auth_router.post(
    "/login",
    responses={401: {"description": "Invalid email or password"}},
)
async def login(
    data: LoginRequest,
    auth_service: FromDishka[AuthService],
) -> LoginResponse:
    return await auth_service.authenticate(data)


@dataclass
class UserScheme:
    id: int
    email: str
    name: str
    role: AdminRole


@auth_router.get(
    "/me",
    dependencies=[bearer_scheme],
    responses={
        401: {"description": "Authorization error"},
        404: {"description": "User not found"},
    },
)
async def me(idp: FromDishka[IdProvider]) -> UserScheme:
    user = await idp.authorize()
    return UserScheme(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
    )


@auth_router.post("/refresh")
async def refresh(
    auth_service: FromDishka[AuthService], data: RefreshTokenRequest
) -> RefreshTokenResponse:
    return await auth_service.refresh_token(data)


@auth_router.post("/logout", status_code=204, dependencies=[bearer_scheme])
async def logout(
    auth_service: FromDishka[AuthService], idp: FromDishka[IdProvider]
) -> None:
    await auth_service.logout(LogoutRequest(access_token=idp.jwt_token))
