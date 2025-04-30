from dataclasses import dataclass

from pydantic import EmailStr


@dataclass
class RegisterUserRequest:
    email: EmailStr
    name: str
    password: str


@dataclass
class RegisterUserResponse:
    access_token: str
    refresh_token: str


@dataclass
class LoginRequest:
    email: EmailStr
    password: str


@dataclass
class LoginResponse:
    access_token: str
    refresh_token: str


@dataclass
class RefreshTokenRequest:
    refresh_token: str


@dataclass
class LogoutRequest:
    access_token: str


@dataclass
class RefreshTokenResponse:
    access_token: str
