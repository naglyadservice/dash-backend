from sqlalchemy import select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.controllers.controller import Controller
from dash.models.controllers.water_vending import WaterVendingController


class WaterVendingControllerRepository(BaseRepository):
    async def get(self, controller_id: int) -> WaterVendingController | None:
        return await self.session.get(WaterVendingController, controller_id)

    async def get_by_device_id(self, device_id: str) -> WaterVendingController | None:
        query = select(WaterVendingController).where(
            WaterVendingController.device_id == device_id
        )
        return await self.session.scalar(query)
