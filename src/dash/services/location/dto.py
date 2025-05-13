from uuid import UUID

from pydantic import BaseModel

from dash.services.common.pagination import Pagination


class CreateLocationRequest(BaseModel):
    company_id: UUID
    name: str
    address: str | None


class CreateLocationResponse(BaseModel):
    location_id: UUID


class LocationAddControllerRequest(BaseModel):
    location_id: UUID
    controller_id: UUID


class LocationOwnerDTO(BaseModel):
    id: UUID
    name: str
    email: str


class CompanyDTO(BaseModel):
    id: UUID
    name: str


class LocationScheme(BaseModel):
    id: UUID
    name: str
    address: str | None
    company: CompanyDTO


class ReadLocationListRequest(Pagination):
    company_id: UUID | None = None


class ReadLocationListResponse(BaseModel):
    locations: list[LocationScheme]
    total: int
