from typing import Callable, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.types import ExceptionHandler

from dash.infrastructure.auth.errors import AuthError, InvalidVerificationCodeError
from dash.infrastructure.s3 import S3UploadError
from dash.services.common.errors.base import (
    AccessDeniedError,
    AccessForbiddenError,
    ConflictError,
    EntityNotFoundError,
    ValidationError,
)
from dash.services.common.errors.controller import (
    ControllerResponseError,
    ControllerTimeoutError,
)
from dash.services.common.errors.user import (
    EmailAlreadyTakenError,
    PhoneNumberAlreadyTakenError,
)


def build_response(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": message})


def register_handler(app: FastAPI, error_type: type[Exception], handler):
    app.add_exception_handler(error_type, cast(ExceptionHandler, handler))


def email_already_taken_error_handler(
    request: Request, exc: EmailAlreadyTakenError
) -> JSONResponse:
    return build_response(409, exc.message)


def phone_number_already_taken_error_handler(
    request: Request, exc: PhoneNumberAlreadyTakenError
) -> JSONResponse:
    return build_response(409, exc.message)


def conflict_error_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return build_response(409, exc.message)


def authentication_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    return build_response(401, exc.message)


def invalid_verification_code_error_handler(
    request: Request, exc: InvalidVerificationCodeError
) -> JSONResponse:
    return build_response(400, exc.message)


def not_found_error_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
    return build_response(404, exc.message)


def controller_response_error_handler(
    request: Request, exc: ControllerResponseError
) -> JSONResponse:
    return build_response(502, exc.message)


def controller_timeout_error_handler(
    request: Request, exc: ControllerTimeoutError
) -> JSONResponse:
    return build_response(504, exc.message)


def access_denied_error_handler(
    request: Request, exc: AccessDeniedError
) -> JSONResponse:
    return build_response(403, exc.message)


def access_forbidden_error_handler(
    request: Request, exc: AccessForbiddenError
) -> JSONResponse:
    return build_response(404, exc.message)


def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return build_response(400, exc.message)


def upload_file_error_handler(request: Request, exc: S3UploadError) -> JSONResponse:
    return build_response(503, exc.message)


def setup_exception_handlers(app: FastAPI) -> None:
    exc_handler_list: list[tuple[type[Exception], Callable]] = [
        (EmailAlreadyTakenError, email_already_taken_error_handler),
        (PhoneNumberAlreadyTakenError, phone_number_already_taken_error_handler),
        (AuthError, authentication_error_handler),
        (EntityNotFoundError, not_found_error_handler),
        (ControllerResponseError, controller_response_error_handler),
        (ControllerTimeoutError, controller_timeout_error_handler),
        (S3UploadError, upload_file_error_handler),
        (AccessDeniedError, access_denied_error_handler),
        (AccessForbiddenError, access_forbidden_error_handler),
        (ValidationError, validation_error_handler),
        (ConflictError, conflict_error_handler),
        (InvalidVerificationCodeError, invalid_verification_code_error_handler),
    ]
    for exc, handler in exc_handler_list:
        register_handler(app, exc, handler)
