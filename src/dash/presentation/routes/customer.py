from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.customer.dto import (
    ChangeCustomerPasswordRequest,
    CreateCustomerRequest,
    CreateCustomerResponse,
    CustomerProfileResponse,
    DeleteCustomerRequest,
    EditCustomerDTO,
    EditCustomerRequest,
    ReadCustomerListRequest,
    ReadCustomerListResponse,
    UpdateCustomerProfileRequest,
)
from dash.services.customer.service import CustomerService

customer_router = APIRouter(
    prefix="/customers",
    tags=["CUSTOMERS"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
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


@customer_router.get("/me", dependencies=[bearer_scheme])
async def get_customer_profile(
    service: FromDishka[CustomerService],
) -> CustomerProfileResponse:
    return await service.read_profile()


@customer_router.patch("/me", dependencies=[bearer_scheme], status_code=204)
async def update_customer_profile(
    service: FromDishka[CustomerService],
    data: UpdateCustomerProfileRequest,
) -> None:
    await service.update_profile(data)


@customer_router.patch("/me/password", status_code=204, dependencies=[bearer_scheme])
async def change_customer_password(
    service: FromDishka[CustomerService],
    data: ChangeCustomerPasswordRequest,
) -> None:
    await service.change_password(data)
