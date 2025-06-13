from dataclasses import dataclass

from dash.services.common.errors.base import ValidationError


@dataclass
class AuthError(Exception):
    message: str = "Auth error"


class InvalidCredentialsError(AuthError):
    message: str = "Invalid credentials"


class JWTTokenError(AuthError):
    message: str


class UserNotFoundError(AuthError):
    message: str = "User not found"


class CustomerNotFoundError(AuthError):
    message: str = "Customer not found"


@dataclass
class InvalidVerificationCodeError(ValidationError):
    message: str = "Invalid verification code"
