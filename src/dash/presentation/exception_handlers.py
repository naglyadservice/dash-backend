from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dash.infrastructure.auth.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from dash.infrastructure.auth.id_provider import AuthenticationError, UserNotFoundError
from dash.services.errors import (
    ControllerNotFoundError,
    ControllerResponseError,
    ControllerTimeoutError,
)


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


def controller_not_found_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Controller not found"})


def controller_response_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=502, content={"detail": "Controller response error"}
    )


def controller_timeout_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=504, content={"detail": "Controller timeout"})


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        EmailAlreadyRegisteredError, email_already_registered_error_handler
    )
    app.add_exception_handler(
        InvalidCredentialsError, invalid_credentials_error_handler
    )
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(UserNotFoundError, user_not_found_error_handler)
    app.add_exception_handler(
        ControllerNotFoundError, controller_not_found_error_handler
    )
    app.add_exception_handler(
        ControllerResponseError, controller_response_error_handler
    )
    app.add_exception_handler(ControllerTimeoutError, controller_timeout_error_handler)
