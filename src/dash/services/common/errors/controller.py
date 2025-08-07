from dataclasses import dataclass

from dash.services.common.errors.base import (
    ApplicationError,
    ConflictError,
    EntityNotFoundError,
    ValidationError,
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


@dataclass
class DeviceIDAlreadyTakenError(ConflictError):
    message: str = "Device id already taken"


@dataclass
class ControllerIsBusyError(ValidationError):
    message: str = "Controller is busy"
