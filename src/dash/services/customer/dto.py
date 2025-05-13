from uuid import UUID
from pydantic import BaseModel, EmailStr


class CreateCustomerRequest(BaseModel):
    company_id: UUID
    name: str
    email: EmailStr | None
    card_id: str | None
    balance: float


class CreateCustomerResponse(BaseModel):
    id: UUID


class EditCustomerRequest(BaseModel):
    id: UUID
    name: str | None = None
    email: EmailStr | None = None
    card_id: str | None = None
    balance: float | None = None


class DeleteCustomerRequest(BaseModel):
    id: UUID
