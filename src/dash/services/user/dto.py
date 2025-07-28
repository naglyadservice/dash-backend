from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

from dash.models.admin_user import AdminRole
from dash.services.common.dto import LocationDTO
from dash.services.common.errors.base import ValidationError


class CreateUserRequest(BaseModel):
    email: str
    name: str


class CreateUserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    password: str


class UserDTO(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: AdminRole
    locations: list[LocationDTO] | None

    model_config = ConfigDict(from_attributes=True)


class ReadUserListResponse(BaseModel):
    users: list[UserDTO]


class AddLocationAdminRequest(BaseModel):
    location_id: UUID
    user_id: UUID | None
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
    location_id: UUID
    user_id: UUID


class DeleteUserRequest(BaseModel):
    id: UUID


class RegeneratePasswordRequest(BaseModel):
    id: UUID


class RegeneratePasswordResponse(BaseModel):
    new_password: str


class SetMessageRequest(BaseModel):
    id: UUID
    message: str | None
