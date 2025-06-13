from dataclasses import dataclass

from dash.services.common.errors.base import ConflictError, EntityNotFoundError


@dataclass
class UserNotFoundError(EntityNotFoundError):
    message: str = "User not found"


@dataclass
class EmailAlreadyTakenError(ConflictError):
    message: str = "Email already taken"


@dataclass
class CardIdAlreadyTakenError(ConflictError):
    message: str = "Card ID already taken"


@dataclass
class CustomerNotFoundError(EntityNotFoundError):
    message: str = "Customer not found"


@dataclass
class PhoneNumberAlreadyTakenError(ConflictError):
    message: str = "Phone number already taken"
