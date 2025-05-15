from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.services.customer.customer import CustomerService
from dash.services.customer.dto import (
    CreateCustomerRequest,
    CreateCustomerResponse,
    DeleteCustomerRequest,
    EditCustomerDTO,
    EditCustomerRequest,
    ReadCustomerListRequest,
    ReadCustomerListResponse,
)

customer_router = APIRouter(
    prefix="/customers", tags=["CUSTOMERS"], route_class=DishkaRoute
)


@customer_router.post("")
async def create_customer(
    service: FromDishka[CustomerService], data: CreateCustomerRequest
) -> CreateCustomerResponse:
    return await service.create_customer(data)


@customer_router.get("")
async def read_customers(
    service: FromDishka[CustomerService], data: ReadCustomerListRequest = Depends()
) -> ReadCustomerListResponse:
    return await service.read_customers(data)


@customer_router.patch("/{id}", status_code=204)
async def edit_customer(
    service: FromDishka[CustomerService], data: EditCustomerDTO, id: UUID
) -> None:
    await service.edit_customer(EditCustomerRequest(id=id, user=data))


@customer_router.delete("/{id}", status_code=204)
async def delete_customer(
    service: FromDishka[CustomerService], data: DeleteCustomerRequest = Depends()
) -> None:
    await service.delete_customer(data)
