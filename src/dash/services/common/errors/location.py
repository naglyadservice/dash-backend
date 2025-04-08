from dataclasses import dataclass

from dash.services.common.errors.base import EntityNotFoundError


@dataclass
class LocationNotFoundError(EntityNotFoundError):
    message: str = "Location not found"
