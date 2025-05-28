from dataclasses import dataclass

from dash.services.common.errors.base import (
    ApplicationError,
    ConflictError,
    EntityNotFoundError,
)


@dataclass
class ControllerNotFoundError(EntityNotFoundError):
    message: str = "Controller not found"


@dataclass
class ControllerTimeoutError(ApplicationError):
    message: str = "Controller timeout"


@dataclass
class ControllerResponseError(ApplicationError):
    message: str = "Controller response error"


@dataclass
class TasmotaIDAlreadyTakenError(ConflictError):
    message: str = "Tasmota id already taken"
