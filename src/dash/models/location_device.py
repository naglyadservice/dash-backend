from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from dash.models.base import Base


class LocationDevice(Base):
    __tablename__ = "location_devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE")
    )
    controller_id: Mapped[str] = mapped_column(
        ForeignKey("controllers.id", ondelete="CASCADE")
    )
