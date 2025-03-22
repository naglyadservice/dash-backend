from typing import Any, Sequence

from sqlalchemy import ColumnElement, func, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.controllers.controller import Controller
from dash.models.controllers.water_vending import WaterVendingController
from dash.services.controller.dto import ReadControllerRequest


class ControllerRepository(BaseRepository):
    async def get_vending_by_device_id(
        self, device_id: str
    ) -> WaterVendingController | None:
        query = select(WaterVendingController).where(
            WaterVendingController.device_id == device_id
        )
        return await self.session.scalar(query)

    async def get_vending(self, controller_id: int) -> WaterVendingController | None:
        query = select(WaterVendingController).where(
            WaterVendingController.id == controller_id
        )
        return await self.session.scalar(query)

    async def get_list(
        self, data: ReadControllerRequest
    ) -> tuple[Sequence[Controller], int]:
        query = select(Controller).offset(data.offset).limit(data.limit)
        if data.type is not None:
            query = query.where(Controller.type == data.type)

        result = await self.session.scalars(query)
        return result.all(), await self._get_count(query.whereclause)

    async def _get_count(self, whereclause: ColumnElement[Any] | None) -> int:
        query = select(func.count()).select_from(Controller)

        if whereclause is not None:
            query = query.where(whereclause)

        result = await self.session.execute(query)
        return result.scalar_one()
