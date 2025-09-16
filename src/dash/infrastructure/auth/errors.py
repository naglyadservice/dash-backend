from dataclasses import dataclass

from dash.services.common.errors.base import (
    AccessDeniedError,
    ApplicationError,
    ValidationError,
)


@dataclass
class AuthError(ApplicationError):
    message: str = "Auth error"


@dataclass
class InvalidCredentialsError(AuthError):
    message: str = "Invalid credentials"


@dataclass
class JWTExpiredError(AuthError):
    message: str = "JWT has expired"


@dataclass
class JWTRevokedError(AuthError):
    message: str = "JWT has been revoked"


@dataclass
class JWTMissingError(AuthError):
    message: str = "JWT is missing"


@dataclass
class JWTInvalidError(AuthError):
    message: str = "JWT is invalid"


@dataclass
class AuthUserNotFoundError(AuthError):
    message: str = "User not found"


@dataclass
class CustomerNotFoundError(AuthError):
    message: str = "Customer not found"


@dataclass
class InvalidVerificationCodeError(ValidationError):
    message: str = "Invalid verification code"


@dataclass
class UserIsBlockedError(AccessDeniedError):
    message = "User is blocked"
