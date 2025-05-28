from datetime import date
from uuid import UUID

from sqlalchemy import exists, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.energy_state import DailyEnergyState


class EnergyStateRepository(BaseRepository):
    async def exists_by_date(self, date_: date, controller_id: UUID) -> bool:
        stmt = select(
            exists(DailyEnergyState).where(
                DailyEnergyState.date == date_,
                DailyEnergyState.controller_id == controller_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
