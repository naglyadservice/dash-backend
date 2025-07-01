from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, exists, select
from sqlalchemy.orm import selectin_polymorphic

from dash.infrastructure.repositories.base import BaseRepository
from dash.models.company import Company
from dash.models.controllers.carwash import CarwashController
from dash.models.controllers.controller import Controller
from dash.models.controllers.fiscalizer import FiscalizerController
from dash.models.controllers.water_vending import WaterVendingController
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin
from dash.services.controller.dto import ReadControllerListRequest


class ControllerRepository(BaseRepository):
    async def get(
        self, controller_id: UUID, company_id: UUID | None = None
    ) -> Controller | None:
        stmt = select(Controller).where(
            Controller.id == controller_id,
        )
        if company_id:
            stmt = stmt.where(Controller.company_id == company_id)

        return await self.session.scalar(stmt)

    async def get_concrete(
        self, controller_id: UUID
    ) -> WaterVendingController | CarwashController | FiscalizerController | None:
        loader_opt = selectin_polymorphic(
            Controller,
            [WaterVendingController, CarwashController, FiscalizerController],
        )
        stmt = (
            select(Controller).where(Controller.id == controller_id).options(loader_opt)
        )
        return await self.session.scalar(stmt)  # type: ignore

    async def get_list_concrete(
        self, location_id: UUID | None = None
    ) -> tuple[
        Sequence[CarwashController | WaterVendingController | FiscalizerController], int
    ]:
        loader_opt = selectin_polymorphic(
            Controller,
            [WaterVendingController, CarwashController, FiscalizerController],
        )
        stmt = select(Controller)
        if location_id:
            stmt = stmt.where(Controller.location_id == location_id)

        paginated_stmt = stmt.options(loader_opt).order_by(Controller.created_at.desc())

        paginated = (await self.session.scalars(paginated_stmt)).unique().all()
        total = await self._get_count(stmt)

        return paginated, total  # type: ignore

    async def get_by_device_id(self, device_id: str) -> Controller | None:
        stmt = select(Controller).where(
            Controller.device_id == device_id,
        )
        return await self.session.scalar(stmt)

    async def exists_by_qr(self, qr: str) -> bool:
        stmt = select(exists().where(Controller.qr == qr))
        return (await self.session.execute(stmt)).scalar_one()

    async def get_concrete_by_qr(
        self, qr: str
    ) -> WaterVendingController | CarwashController | FiscalizerController | None:
        loader_opt = selectin_polymorphic(
            Controller,
            [WaterVendingController, CarwashController, FiscalizerController],
        )
        stmt = select(Controller).where(Controller.qr == qr).options(loader_opt)
        return await self.session.scalar(stmt)  # type: ignore

    async def get_by_tasmota_id(self, tasmota_id: str) -> Controller | None:
        stmt = select(Controller).where(
            Controller.tasmota_id == tasmota_id,
        )
        return await self.session.scalar(stmt)

    async def get_wsm(self, controller_id: UUID) -> WaterVendingController | None:
        stmt = select(WaterVendingController).where(
            WaterVendingController.id == controller_id
        )
        return await self.session.scalar(stmt)

    async def get_wsm_by_device_id(
        self, device_id: str
    ) -> WaterVendingController | None:
        stmt = select(WaterVendingController).where(
            WaterVendingController.device_id == device_id,
        )
        return await self.session.scalar(stmt)

    async def get_carwash(self, controller_id: UUID) -> CarwashController | None:
        stmt = select(CarwashController).where(CarwashController.id == controller_id)
        return await self.session.scalar(stmt)

    async def get_carwash_by_device_id(
        self, device_id: str
    ) -> CarwashController | None:
        stmt = select(CarwashController).where(CarwashController.device_id == device_id)
        return await self.session.scalar(stmt)

    async def get_fiscalizer(self, controller_id: UUID) -> FiscalizerController | None:
        stmt = select(FiscalizerController).where(
            FiscalizerController.id == controller_id
        )
        return await self.session.scalar(stmt)

    async def get_fiscalizer_by_device_id(
        self, device_id: str
    ) -> FiscalizerController | None:
        stmt = select(FiscalizerController).where(
            FiscalizerController.device_id == device_id
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

        if data.company_id is not None:
            stmt = stmt.where(Controller.company_id == data.company_id)

        elif data.location_id is not None:
            stmt = stmt.where(Controller.location_id == data.location_id)

        elif whereclause is not None:
            stmt = stmt.where(whereclause)

        paginated_stmt = (
            stmt.order_by(Controller.created_at.desc())
            .offset(data.offset)
            .limit(data.limit)
        )

        paginated = (await self.session.scalars(paginated_stmt)).unique().all()
        total = await self._get_count(stmt)

        return paginated, total

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
            select(LocationAdmin.location_id).where(LocationAdmin.user_id == user_id)
        )
        return await self._get_list(data, whereclause)
