from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dash.infrastructure.auth.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from dash.infrastructure.auth.id_provider import AuthenticationError, UserNotFoundError


def email_already_registered_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Email already registered"})


def invalid_credentials_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=401, content={"detail": "Invalid email or password"}
    )


def authentication_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": "Invalid session"})


def user_not_found_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "User not found"})


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        EmailAlreadyRegisteredError, email_already_registered_error_handler
    )
    app.add_exception_handler(
        InvalidCredentialsError, invalid_credentials_error_handler
    )
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(UserNotFoundError, user_not_found_error_handler)
