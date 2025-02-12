from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .controller import Controller, ControllerType


class CarwashСontroller(Controller):
    __tablename__ = "carwash_controllers"

    controller_id: Mapped[int] = mapped_column(
        ForeignKey("controllers.id"), primary_key=True
    )

    __mapper_args__ = {"polymorphic_identity": ControllerType.CARWASH.value}
