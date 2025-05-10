import enum
from datetime import datetime
from typing import Annotated, Any, TypeAlias
from uuid import UUID

from sqlalchemy import ARRAY, BigInteger, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry

Int16: TypeAlias = Annotated[int, 16]
Int64: TypeAlias = Annotated[int, 64]


class Base(DeclarativeBase):
    registry = registry(
        type_annotation_map={
            dict[str, Any]: JSONB,
            list[str]: ARRAY(String),
            Int16: Integer,
            Int64: BigInteger,
            datetime: DateTime(timezone=True),
            UUID: PG_UUID(as_uuid=True),
            enum.Enum: ENUM(enum.Enum),
        }
    )

    def __repr__(self):
        columns = ", ".join(
            f"{column.name}={getattr(self, column.name)!r}"
            for column in self.__table__.columns
        )
        return f"{self.__class__.__name__}({columns})"

    def __str__(self):
        return self.__repr__()


class TimestampMixin:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=func.now(),
    )
