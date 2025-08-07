from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from dash.infrastructure.repositories.base import BaseRepository
from dash.models import Encashment
from dash.services.controller.dto import ReadEncashmentListRequest


class EncashmentRepository(BaseRepository):
    async def get(self, encashment_id: UUID, controller_id: UUID) -> Encashment | None:
        stmt = select(Encashment).where(
            Encashment.id == encashment_id, Encashment.controller_id == controller_id
        )
        return await self.session.scalar(stmt)

    async def get_list(
        self, data: ReadEncashmentListRequest
    ) -> tuple[Sequence[Encashment], int]:
        stmt = select(Encashment).where(Encashment.controller_id == data.controller_id)

        paginated_stmt = (
            stmt.order_by(Encashment.is_closed.desc())
            .offset(data.offset)
            .limit(data.limit)
        )
        paginated = (await self.session.scalars(paginated_stmt)).unique().all()
        total = await self._get_count(stmt)

        return paginated, total
