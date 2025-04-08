from typing import Any

from pydantic import BaseModel, EmailStr, model_validator

from dash.models.user import UserRole
from dash.services.common.errors.base import ValidationError


class CreateUserRequest(BaseModel):
    email: str
    name: str


class CreateUserResponse(BaseModel):
    id: int
    email: str
    name: str
    password: str


class LocationDTO(BaseModel):
    id: int
    name: str


class UserDTO(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    locations: list[LocationDTO] | None


class ReadUserListResponse(BaseModel):
    users: list[UserDTO]


class AddLocationAdminRequest(BaseModel):
    location_id: int
    user_id: int | None
    user: CreateUserRequest | None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("user_id") is None and values.get("user") is None:
            raise ValidationError("Either 'user_id' or 'user' is required")
        return values


class AddLocationAdminResponse(BaseModel):
    user: CreateUserResponse | None


class RemoveLocationAdminRequest(BaseModel):
    location_id: int
    user_id: int
