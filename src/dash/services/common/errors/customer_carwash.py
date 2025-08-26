from dataclasses import dataclass

from dash.services.common.errors.base import (
    ConflictError,
    EntityNotFoundError,
)


@dataclass
class CarwashSessionActiveError(ConflictError):
    message: str = "Carwash session is already active"


@dataclass
class CarwashSessionNotFoundError(EntityNotFoundError):
    message: str = "Carwash session not found"
