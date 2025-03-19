from typing import Any

from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, registry


class Base(DeclarativeBase):
    registry = registry(
        type_annotation_map={
            dict[str, Any]: JSON,
        }
    )
