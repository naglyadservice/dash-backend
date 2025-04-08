from dataclasses import dataclass


@dataclass
class ApplicationError(Exception):
    message: str


@dataclass
class EntityNotFoundError(ApplicationError):
    message: str = "Entity not found"


@dataclass
class AccessDeniedError(ApplicationError):
    message: str = "Access denied"


@dataclass
class AccessForbiddenError(ApplicationError):
    message: str = "Resource not found"


@dataclass
class ValidationError(ApplicationError):
    pass
