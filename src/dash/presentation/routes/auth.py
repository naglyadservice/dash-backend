from datetime import datetime
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from pydantic import BaseModel

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
from dash.infrastructure.auth.errors import (
    AuthUserNotFoundError,
    InvalidCredentialsError,
    InvalidVerificationCodeError,
    JWTExpiredError,
    JWTInvalidError,
    JWTMissingError,
    JWTRevokedError,
)
from dash.infrastructure.auth.id_provider import IdProvider
from dash.models.admin_user import AdminRole
from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses
from dash.services.common.errors.company import CompanyNotFoundError
from dash.services.common.errors.user import (
    CustomerNotFoundError,
    PhoneNumberAlreadyTakenError,
)

auth_router = APIRouter(prefix="/auth", tags=["AUTH"], route_class=DishkaRoute)


@auth_router.post(
    "/login",
    responses=build_responses((401, (InvalidCredentialsError,))),
)
async def login(
    data: LoginRequest,
    auth_service: FromDishka[AuthService],
) -> LoginResponse:
    return await auth_service.authenticate(data)


@auth_router.post(
    "/customer/login",
    responses=build_responses((401, (InvalidCredentialsError,))),
)
async def login_customer(
    data: LoginCustomerRequest,
    auth_service: FromDishka[AuthService],
) -> LoginResponse:
    return await auth_service.authenticate_customer(data)


class UserScheme(BaseModel):
    id: UUID
    email: str
    name: str
    role: AdminRole
    subscription_paid_until: datetime | None
    subscription_payment_details: str | None
    subscription_amount: int | None
    is_blocked: bool


@auth_router.get(
    "/me",
    dependencies=[bearer_scheme],
    responses=build_responses(
        (
            401,
            (
                JWTExpiredError,
                JWTRevokedError,
                JWTMissingError,
                JWTInvalidError,
                AuthUserNotFoundError,
            ),
        ),
    ),
)
async def me(idp: FromDishka[IdProvider]) -> UserScheme:
    user = await idp.authorize()
    return UserScheme.model_validate(user, from_attributes=True)


@auth_router.post(
    "/refresh",
    responses=build_responses(
        (401, (JWTExpiredError, JWTInvalidError)),
    ),
)
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
    responses=build_responses(
        (404, (CompanyNotFoundError,)), (409, (PhoneNumberAlreadyTakenError,))
    ),
)
async def start_customer_registration(
    data: RegisterCustomerRequest,
    auth_service: FromDishka[AuthService],
) -> None:
    await auth_service.start_customer_registration(data)


@auth_router.post(
    "/customer/register/complete",
    responses=build_responses(
        (400, (InvalidVerificationCodeError,)), (409, (PhoneNumberAlreadyTakenError,))
    ),
)
async def complete_customer_registration(
    data: CompleteCustomerRegistrationRequest,
    auth_service: FromDishka[AuthService],
) -> CustomerRegistrationResponse:
    return await auth_service.complete_customer_registration(data)


@auth_router.post(
    "/customer/password-reset/start",
    status_code=204,
    responses=build_responses((404, (CustomerNotFoundError,))),
)
async def start_password_reset(
    data: StartPasswordResetRequest,
    auth_service: FromDishka[AuthService],
) -> None:
    await auth_service.start_password_reset(data)


@auth_router.post(
    "/customer/password-reset/complete",
    status_code=204,
    responses=build_responses(
        (400, (InvalidVerificationCodeError,)), (404, (CustomerNotFoundError,))
    ),
)
async def complete_password_reset(
    data: CompletePasswordResetRequest,
    auth_service: FromDishka[AuthService],
) -> None:
    await auth_service.complete_password_reset(data)
