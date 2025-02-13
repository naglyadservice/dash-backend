from sqlalchemy.ext.asyncio import AsyncSession

from dash.models.base import Base


class SATracker:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, model: Base) -> None:
        self.session.add(model)
