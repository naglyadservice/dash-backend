from typing import Any, Type
from dash.models.base import Base


def parse_model_fields(instance: Base, model: Type[Base]) -> dict[str, Any]:
    return {
        c.name: getattr(instance, c.name)
        for c in model.__table__.columns
        if hasattr(instance, c.name) and getattr(instance, c.name) is not None
    }
