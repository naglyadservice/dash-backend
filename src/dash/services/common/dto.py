from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.services.common.errors.base import ValidationError


class ControllerID(BaseModel):
    controller_id: UUID


class LocationDTO(BaseModel):
    id: UUID
    name: str
    address: str | None

    model_config = ConfigDict(from_attributes=True)


class CompanyDTO(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class PublicLocationDTO(BaseModel):
    id: UUID
    name: str
    address: str | None

    model_config = ConfigDict(from_attributes=True)


class PublicCompanyDTO(BaseModel):
    id: UUID
    name: str
    privacy_policy: str | None
    offer_agreement: str | None
    about: str | None
    logo_key: str | None
    phone_number: str | None
    email: str | None

    model_config = ConfigDict(from_attributes=True)


class BaseFilters(BaseModel):
    controller_id: UUID | None = None
    location_id: UUID | None = None
    company_id: UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        filters = [
            values.get("controller_id"),
            values.get("location_id"),
            values.get("company_id"),
        ]
        active_filters = [f for f in filters if f is not None]

        if len(active_filters) > 1:
            raise ValidationError(
                "Only one filter can be used at a time. Please use either 'controller_id', 'location_id', or 'company_id'"
            )
        return values
