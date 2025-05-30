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
