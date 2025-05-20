from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.user.dto import (
    AddLocationAdminRequest,
    AddLocationAdminResponse,
    DeleteUserRequest,
    ReadUserListResponse,
    RemoveLocationAdminRequest,
)
from dash.services.user.service import UserService

user_router = APIRouter(
    prefix="/users",
    tags=["USERS"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@user_router.get("")
async def read_users(user_service: FromDishka[UserService]) -> ReadUserListResponse:
    return await user_service.read_users()


@user_router.post("/location-admins")
async def add_location_admin(
    user_service: FromDishka[UserService], data: AddLocationAdminRequest
) -> AddLocationAdminResponse:
    return await user_service.add_location_admin(data)


@user_router.delete("/location-admins")
async def remove_admin_from_location(
    user_service: FromDishka[UserService], data: RemoveLocationAdminRequest
) -> None:
    return await user_service.remove_admin_from_location(data)


@user_router.delete("/{id}")
async def delete_user(
    user_service: FromDishka[UserService], data: DeleteUserRequest = Depends()
) -> None:
    return await user_service.delete_user(data)
