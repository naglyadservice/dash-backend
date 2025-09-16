from dataclasses import dataclass
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses
from dash.services.common.errors.location import LocationNotFoundError
from dash.services.common.errors.user import UserNotFoundError
from dash.services.user.dto import (
    AddLocationAdminRequest,
    AddLocationAdminResponse,
    DeleteUserRequest,
    ReadUserListResponse,
    RegeneratePasswordRequest,
    RegeneratePasswordResponse,
    RemoveLocationAdminRequest,
    UpdateOwnerDTO,
    UpdateOwnerRequest,
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


@user_router.post(
    "/location-admins",
    responses=build_responses(
        (
            404,
            (
                UserNotFoundError,
                LocationNotFoundError,
            ),
        )
    ),
)
async def add_location_admin(
    user_service: FromDishka[UserService], data: AddLocationAdminRequest
) -> AddLocationAdminResponse:
    return await user_service.add_location_admin(data)


@user_router.delete(
    "/location-admins",
    responses=build_responses((404, (UserNotFoundError,))),
)
async def remove_admin_from_location(
    user_service: FromDishka[UserService], data: RemoveLocationAdminRequest
) -> None:
    return await user_service.remove_admin_from_location(data)


@user_router.delete(
    "/{id}",
    responses=build_responses((404, (UserNotFoundError,))),
)
async def delete_user(
    user_service: FromDishka[UserService], data: DeleteUserRequest = Depends()
) -> None:
    return await user_service.delete_user(data)


@user_router.patch(
    "/{id}/password", responses=build_responses((404, (UserNotFoundError,)))
)
async def regenerate_password(
    user_service: FromDishka[UserService], data: RegeneratePasswordRequest = Depends()
) -> RegeneratePasswordResponse:
    return await user_service.regenerate_password(data)


@dataclass
class MessageDTO:
    message: str | None


@user_router.put(
    "/{id}/owner",
    status_code=204,
    responses=build_responses((404, (UserNotFoundError,))),
)
async def update_owner(
    user_service: FromDishka[UserService], data: UpdateOwnerDTO, id: UUID
) -> None:
    await user_service.update_owner(UpdateOwnerRequest(id=id, **data.model_dump()))
