from collections import defaultdict
from typing import Type

from dash.services.common.errors.base import ApplicationError
from dash.services.common.errors.controller import (
    ControllerNotFoundError,
    ControllerResponseError,
    ControllerTimeoutError,
)

erros_name_map = {
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    409: "Conflict",
    504: "Gateway Timeout",
    503: "Service Unavailable",
}


def build_responses(*responses: tuple[int, tuple[Type[ApplicationError], ...]]) -> dict:
    grouped_errors = defaultdict(list)
    for status_code, errors in responses:
        grouped_errors[status_code].extend(errors)

    result = {}
    for status_code, errors in grouped_errors.items():
        result[status_code] = {
            "description": erros_name_map.get(status_code),
            "content": {
                "application/json": {
                    "examples": {
                        error.__name__: {"value": {"detail": error.message}}
                        for error in errors
                    }
                }
            },
        }
    return result


controller_errors = (
    (504, (ControllerTimeoutError,)),
    (503, (ControllerResponseError,)),
    (404, (ControllerNotFoundError,)),
)
