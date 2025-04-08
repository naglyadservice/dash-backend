from dataclasses import dataclass


@dataclass
class AuthError(Exception):
    message: str = "Auth error"


class InvalidCredentialsError(AuthError):
    message: str = "Invalid credentials"


class InvalidAuthSessionError(AuthError):
    message: str = "Invalid session"


class UserNotFoundError(AuthError):
    message: str = "User not found"
