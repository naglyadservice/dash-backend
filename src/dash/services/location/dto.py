from typing import Any

from pydantic import BaseModel, model_validator

from dash.services.common.errors.base import ValidationError
from dash.services.user.dto import CreateUserRequest, CreateUserResponse


class CreateLocationRequest(BaseModel):
    owner_id: int | None
    name: str
    address: str | None
    user: CreateUserRequest | None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values.get("owner_id") and not values.get("user"):
            raise ValidationError("Either 'owner_id' or 'user' is required")
        if values.get("owner_id") and values.get("user"):
            raise ValidationError("'owner_id' and 'user' cannot be used together")

        return values


class CreateLocationResponse(BaseModel):
    location_id: int
    user: CreateUserResponse | None


class LocationAddControllerRequest(BaseModel):
    location_id: int
    controller_id: int


class LocationOwnerDTO(BaseModel):
    id: int
    name: str
    email: str


class LocationScheme(BaseModel):
    id: int
    name: str
    address: str | None
    owner: LocationOwnerDTO


class ReadLocationListResponse(BaseModel):
    locations: list[LocationScheme]
