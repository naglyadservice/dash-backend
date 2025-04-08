from dataclasses import dataclass

from dash.services.common.errors.base import ApplicationError, EntityNotFoundError


@dataclass
class UserNotFoundError(EntityNotFoundError):
    message: str = "User not found"


@dataclass
class EmailAlreadyTakenError(ApplicationError):
    message: str = "Email already taken"
