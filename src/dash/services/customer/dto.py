from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from dash.services.common.pagination import Pagination


class CreateCustomerRequest(BaseModel):
    company_id: UUID
    name: str
    email: EmailStr | None
    card_id: str | None
    balance: float


class CreateCustomerResponse(BaseModel):
    id: UUID


class EditCustomerDTO(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    card_id: str | None = None
    balance: float | None = None


class EditCustomerRequest(BaseModel):
    id: UUID
    user: EditCustomerDTO


class DeleteCustomerRequest(BaseModel):
    id: UUID


class CustomerScheme(BaseModel):
    id: UUID
    name: str | None
    email: EmailStr | None
    card_id: str | None
    balance: float

    model_config = ConfigDict(from_attributes=True)


class ReadCustomerListRequest(Pagination):
    company_id: UUID | None = None


class ReadCustomerListResponse(BaseModel):
    customers: list[CustomerScheme]
    total: int
