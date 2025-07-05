from dataclasses import dataclass

from dash.services.common.errors.base import (
    ConflictError,
    EntityNotFoundError,
    ValidationError,
)


@dataclass
class CarwashSessionActiveError(ConflictError):
    message: str = "Carwash session is already active"


@dataclass
class CarwashSessionNotFoundError(EntityNotFoundError):
    message: str = "Carwash session not found"


@dataclass
class InsufficientBalanceError(ValidationError):
    message: str = "Insufficient balance"


@dataclass
class InsufficientDepositAmountError(ValidationError):
    message: str = "Insufficient deposit amount"
