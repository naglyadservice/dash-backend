from dataclasses import dataclass

from dash.services.common.errors.base import EntityNotFoundError


@dataclass
class CompanyNotFoundError(EntityNotFoundError):
    message: str = "Company not found"
