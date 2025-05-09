from pydantic import BaseModel


class CreateLocationRequest(BaseModel):
    company_id: int
    name: str
    address: str | None


class CreateLocationResponse(BaseModel):
    location_id: int


class LocationAddControllerRequest(BaseModel):
    location_id: int
    controller_id: int


class LocationOwnerDTO(BaseModel):
    id: int
    name: str
    email: str


class CompanyDTO(BaseModel):
    id: int
    name: str


class LocationScheme(BaseModel):
    id: int
    name: str
    address: str | None
    company: CompanyDTO


class ReadLocationListResponse(BaseModel):
    locations: list[LocationScheme]
