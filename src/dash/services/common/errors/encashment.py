from dataclasses import dataclass

from dash.services.common.errors.base import ConflictError, EntityNotFoundError


@dataclass
class EncashmentNotFoundError(EntityNotFoundError):
    message: str = "Encashment not found"


@dataclass
class EncashmentAlreadyClosedError(ConflictError):
    message: str = "Encashment already closed"
