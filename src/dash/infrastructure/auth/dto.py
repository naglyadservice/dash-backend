from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, EmailStr


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
class LoginCustomerRequest:
    company_id: UUID
    phone_number: str
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


class RegisterCustomerRequest(BaseModel):
    phone_number: str
    password: str
    company_id: UUID


@dataclass
class CompleteCustomerRegistrationRequest:
    code: str


@dataclass
class CustomerRegistrationResponse:
    access_token: str
    refresh_token: str


class StartPasswordResetRequest(BaseModel):
    phone_number: str
    company_id: UUID


class CompletePasswordResetRequest(BaseModel):
    code: str
    new_password: str
