from dataclasses import dataclass

from dash.services.common.errors.base import (ApplicationError,
                                              EntityNotFoundError)


@dataclass
class ControllerNotFoundError(EntityNotFoundError):
    message: str = "Controller not found"


@dataclass
class ControllerTimeoutError(ApplicationError):
    message: str = "Controller timeout"


@dataclass
class ControllerResponseError(ApplicationError):
    message: str = "Controller response error"
