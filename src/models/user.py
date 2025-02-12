from enum import Enum

from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class UserRole(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column()
    password_hash: Mapped[str] = mapped_column()
    role: Mapped[UserRole] = mapped_column()
