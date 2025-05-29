from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import exists, func, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.energy_state import DailyEnergyState
from dash.services.controller.dto import GetEnergyStatsRequest, GetEnergyStatsResponse


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

    async def get_stats(self, data: GetEnergyStatsRequest) -> GetEnergyStatsResponse:
        now = datetime.now(UTC)

        stmt = select(func.sum(DailyEnergyState.energy)).where(
            DailyEnergyState.controller_id == data.controller_id,
            DailyEnergyState.date >= (now - timedelta(days=data.period)).date(),
            DailyEnergyState.date <= now.date(),
        )
        result = await self.session.execute(stmt)
        return GetEnergyStatsResponse(total_energy=result.scalar_one())
