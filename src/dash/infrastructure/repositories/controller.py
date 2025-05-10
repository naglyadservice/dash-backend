from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.company import Company
from dash.models.controllers.controller import Controller
from dash.models.controllers.water_vending import WaterVendingController
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.services.controller.dto import ReadControllerListRequest


class ControllerRepository(BaseRepository):
    async def get(self, company_id: UUID, controller_id: UUID) -> Controller | None:
        stmt = select(Controller).where(
            Controller.id == controller_id,
            Controller.company_id == company_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_wsm_by_device_id(
        self, device_id: str
    ) -> WaterVendingController | None:
        stmt = select(WaterVendingController).where(
            WaterVendingController.device_id == device_id,
        )
        return await self.session.scalar(stmt)

    async def get_wsm(self, controller_id: UUID) -> WaterVendingController | None:
        stmt = select(WaterVendingController).where(
            WaterVendingController.id == controller_id
        )
        return await self.session.scalar(stmt)

    async def _get_list(
        self,
        data: ReadControllerListRequest,
        whereclause: ColumnElement[Any] | None = None,
    ) -> tuple[Sequence[Controller], int]:
        stmt = select(Controller)

        if data.type is not None:
            stmt = stmt.where(Controller.type == data.type)

        if data.location_id:
            stmt = stmt.where(Controller.location_id == data.location_id)

        if whereclause is not None:
            stmt = stmt.where(whereclause)

        result = await self.session.scalars(stmt)
        return result.all(), await self._get_count(stmt)

    async def get_list_all(
        self, data: ReadControllerListRequest
    ) -> tuple[Sequence[Controller], int]:
        return await self._get_list(data)

    async def get_list_by_owner(
        self, data: ReadControllerListRequest, user_id: UUID
    ) -> tuple[Sequence[Controller], int]:
        whereclause = Controller.location_id.in_(
            select(Location.id).join(Company).where(Company.owner_id == user_id)
        )
        return await self._get_list(data, whereclause)

    async def get_list_by_admin(
        self, data: ReadControllerListRequest, user_id: UUID
    ) -> tuple[Sequence[Controller], int]:
        whereclause = Controller.location_id.in_(
            select(Location.id)
            .outerjoin(LocationAdmin)
            .where(LocationAdmin.user_id == user_id)
        )
        return await self._get_list(data, whereclause)
