from dataclasses import dataclass


@dataclass
class AuthError(Exception):
    message: str = "Auth error"


class InvalidCredentialsError(AuthError):
    message: str = "Invalid credentials"


class JWTTokenError(AuthError):
    message: str


class UserNotFoundError(AuthError):
    message: str = "User not found"
