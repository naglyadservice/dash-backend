from typing import Any
from uuid import UUID

from pydantic import BaseModel, model_validator

from dash.services.common.errors.base import ValidationError
from dash.services.user.dto import CreateUserRequest, CreateUserResponse


class CreateCompanyRequest(BaseModel):
    name: str
    owner_id: UUID | None = None
    new_owner: CreateUserRequest | None = None
    offer_agreement: str | None = None
    privacy_policy: str | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values.get("owner_id") and not values.get("new_owner"):
            raise ValidationError("Either 'owner_id' or 'new_owner' is required")
        if values.get("owner_id") and values.get("new_owner"):
            raise ValidationError("'owner_id' and 'new_owner' cannot be used together")

        return values


class CreateCompanyResponse(BaseModel):
    company_id: UUID
    created_owner: CreateUserResponse | None


class CompanyOwnerDTO(BaseModel):
    id: UUID
    name: str
    email: str


class CompanyScheme(BaseModel):
    id: UUID
    name: str
    owner: CompanyOwnerDTO
    offer_agreement: str | None
    privacy_policy: str | None


class ReadCompanyListResponse(BaseModel):
    companies: list[CompanyScheme]


class EditCompanyDTO(BaseModel):
    name: str | None = None
    offer_agreement: str | None = None
    privacy_policy: str | None = None


class EditCompanyRequest(BaseModel):
    company_id: UUID
    data: EditCompanyDTO
