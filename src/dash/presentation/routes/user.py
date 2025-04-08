from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from dash.services.user.dto import (
    AddLocationAdminRequest,
    AddLocationAdminResponse,
    ReadUserListResponse,
    RemoveLocationAdminRequest,
)
from dash.services.user.user import UserService

user_router = APIRouter(prefix="/users", tags=["USERS"], route_class=DishkaRoute)


@user_router.get("")
async def read_users(user_service: FromDishka[UserService]) -> ReadUserListResponse:
    return await user_service.read_users()


@user_router.post("/location-admins")
async def add_location_admin(
    user_service: FromDishka[UserService], data: AddLocationAdminRequest
) -> AddLocationAdminResponse:
    return await user_service.add_location_admin(data)


@user_router.delete("/location-admins")
async def remove_location_admin(
    user_service: FromDishka[UserService], data: RemoveLocationAdminRequest
) -> None:
    return await user_service.remove_location_admin(data)
