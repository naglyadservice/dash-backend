from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from dash.infrastructure.auth.auth_service import (
    AuthService,
    LoginRequest,
    RegisterUserRequest,
    RegisterUserResponse,
    UserScheme,
)
from dash.infrastructure.auth.id_provider import IdProvider

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
    status_code=200,
    responses={401: {"description": "Invalid email or password"}},
)
async def login(
    request: Request,
    data: LoginRequest,
    auth_service: FromDishka[AuthService],
) -> JSONResponse:
    session_id = request.cookies.get("session")
    login_response = await auth_service.authenticate(data, session_id)

    response = JSONResponse(content=asdict(login_response.user))
    response.set_cookie(
        key="session",
        value=login_response.session_id,
        expires=datetime.now(UTC) + timedelta(days=90),
        secure=True,
        httponly=True,
        samesite="none",
    )
    return response


@auth_router.get(
    "/me",
    status_code=200,
    responses={
        401: {"description": "Invalid session"},
        404: {"description": "User not found"},
    },
)
async def me(idp: FromDishka[IdProvider]) -> UserScheme:
    user = await idp.get_current_user()
    return UserScheme(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
    )


@auth_router.post("/logout", status_code=204)
async def logout(request: Request, auth_service: FromDishka[AuthService]) -> Response:
    await auth_service.logout(request.cookies.get("session"))

    response = Response(status_code=204)
    response.delete_cookie("session")

    return response
