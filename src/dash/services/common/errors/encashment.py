from dash.services.common.errors.base import ConflictError, EntityNotFoundError


class EncashmentNotFoundError(EntityNotFoundError):
    model_name: str = "Encashment"


class EncashmentAlreadyClosedError(ConflictError):
    message: str = "Encashment already closed"
