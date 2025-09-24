from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from dash.infrastructure.repositories.base import BaseRepository
from dash.infrastructure.repositories.utils import parse_model_fields
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

    async def insert_with_conflict_ignore(self, model: Encashment) -> bool:
        insert_tx = (
            insert(Encashment)
            .values(
                **parse_model_fields(model, Encashment),
            )
            .on_conflict_do_nothing(
                constraint="uix_encashment_controller_encashment_id"
            )
            .returning(Encashment.id)
        )
        result = await self.session.execute(insert_tx)
        inserted_id = result.scalar_one_or_none()

        return inserted_id is not None
