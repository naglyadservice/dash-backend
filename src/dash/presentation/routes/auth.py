from dataclasses import dataclass
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from dash.infrastructure.auth.auth_service import (
    AuthService,
    LoginRequest,
    LoginResponse,
)
from dash.infrastructure.auth.dto import (
    CompleteCustomerRegistrationRequest,
    CompletePasswordResetRequest,
    CustomerRegistrationResponse,
    LoginCustomerRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterCustomerRequest,
    StartPasswordResetRequest,
)
from dash.infrastructure.auth.id_provider import IdProvider
from dash.models.admin_user import AdminRole
from dash.presentation.bearer import bearer_scheme

auth_router = APIRouter(prefix="/auth", tags=["AUTH"], route_class=DishkaRoute)


@auth_router.post(
    "/login",
    responses={401: {"description": "Invalid email or password"}},
)
async def login(
    data: LoginRequest,
    auth_service: FromDishka[AuthService],
) -> LoginResponse:
    return await auth_service.authenticate(data)


@auth_router.post(
    "/customer/login",
    responses={401: {"description": "Invalid email or password"}},
)
async def login_customer(
    data: LoginCustomerRequest,
    auth_service: FromDishka[AuthService],
) -> LoginResponse:
    return await auth_service.authenticate_customer(data)


@dataclass
class UserScheme:
    id: UUID
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


@auth_router.post(
    "/customer/register/start",
    status_code=204,
    responses={409: {"description": "Phone number already taken"}},
)
async def start_customer_registration(
    data: RegisterCustomerRequest,
    auth_service: FromDishka[AuthService],
) -> None:
    await auth_service.start_customer_registration(data)


@auth_router.post(
    "/customer/register/complete",
    responses={
        400: {"description": "Invalid verification code"},
        409: {"description": "Phone number already taken"},
    },
)
async def complete_customer_registration(
    data: CompleteCustomerRegistrationRequest,
    auth_service: FromDishka[AuthService],
) -> CustomerRegistrationResponse:
    return await auth_service.complete_customer_registration(data)


@auth_router.post(
    "/customer/password-reset/start",
    status_code=204,
    responses={404: {"description": "Customer not found"}},
)
async def start_password_reset(
    data: StartPasswordResetRequest,
    auth_service: FromDishka[AuthService],
) -> None:
    await auth_service.start_password_reset(data)


@auth_router.post(
    "/customer/password-reset/complete",
    status_code=204,
    responses={
        400: {"description": "Invalid verification code"},
        404: {"description": "Customer not found"},
    },
)
async def complete_password_reset(
    data: CompletePasswordResetRequest,
    auth_service: FromDishka[AuthService],
) -> None:
    await auth_service.complete_password_reset(data)
