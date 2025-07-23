from uuid import UUID

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)
