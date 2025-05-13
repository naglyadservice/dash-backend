from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from dash.services.common.pagination import Pagination


class BaseCustomer(BaseModel):
    name: str
    company_id: UUID
    card_id: str
    balance: float
    email: EmailStr | None
    birth_date: date | None
    phone_number: str | None
    discount_percent: int | None
    tariff_per_liter_1: float | None
    tariff_per_liter_2: float | None


class CreateCustomerRequest(BaseCustomer):
    pass


class CreateCustomerResponse(BaseModel):
    id: UUID


class EditCustomerDTO(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    card_id: str | None = None
    balance: float | None = None
    birth_date: date | None = None
    phone_number: str | None = None
    discount_percent: int | None = None
    tariff_per_liter_1: float | None = None
    tariff_per_liter_2: float | None = None


class EditCustomerRequest(BaseModel):
    id: UUID
    user: EditCustomerDTO


class DeleteCustomerRequest(BaseModel):
    id: UUID


class CustomerScheme(BaseCustomer):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class ReadCustomerListRequest(Pagination):
    company_id: UUID | None = None


class ReadCustomerListResponse(BaseModel):
    customers: list[CustomerScheme]
    total: int
