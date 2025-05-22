import uuid
from dataclasses import dataclass
from datetime import datetime

import pytest
from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.models.admin_user import AdminUser
from dash.models.encashment import Encashment
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.encashment import (
    EncashmentAlreadyClosedError,
    EncashmentNotFoundError,
)
from dash.services.controller.dto import (
    CloseEncashmentRequest,
    ReadEncashmentListRequest,
)
from dash.services.controller.service import ControllerService
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class EncashmentDependencies:
    controller_service: ControllerService
    db_session: AsyncSession


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return EncashmentDependencies(
        controller_service=await request_di_container.get(ControllerService),
        db_session=await request_di_container.get(AsyncSession),
    )


@pytest.fixture
async def encashment(deps: EncashmentDependencies, test_env: TestEnvironment):
    encashment = Encashment(
        controller_id=test_env.controller_1.id,
        coin_1=1,
        coin_2=2,
        coin_3=3,
        coin_4=4,
        coin_5=5,
        coin_6=6,
        bill_1=1,
        bill_2=2,
        bill_3=3,
        bill_4=4,
        bill_5=5,
        bill_6=6,
        bill_7=7,
        bill_8=8,
        encashed_amount=100,
        created_at_controller=datetime(2000, 1, 1),
    )
    deps.db_session.add(encashment)
    await deps.db_session.commit()
    return encashment


@pytest.mark.parametrize(
    "user, error",
    [
        ("superadmin", None),
        ("company_owner_1", None),
        ("location_admin_1", None),
        ("company_owner_2", AccessForbiddenError()),
        ("location_admin_2", AccessForbiddenError()),
    ],
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_read_encashments(
    deps: EncashmentDependencies,
    encashment: Encashment,
    user: AdminUser,
    error: Exception,
):
    try:
        response = await deps.controller_service.read_encashments(
            ReadEncashmentListRequest(controller_id=encashment.controller_id)
        )
    except Exception as e:
        assert error == e
    else:
        assert response.total == 1


@pytest.mark.parametrize(
    "user, error",
    [
        ("superadmin", None),
        ("company_owner_1", None),
        ("location_admin_1", None),
        ("company_owner_2", AccessForbiddenError()),
        ("location_admin_2", AccessForbiddenError()),
    ],
    indirect=["user"],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_close_encashment(
    deps: EncashmentDependencies,
    encashment: Encashment,
    user: AdminUser,
    error: Exception,
):
    dto = CloseEncashmentRequest(
        controller_id=encashment.controller_id,
        encashment_id=encashment.id,
        received_amount=90,
    )
    try:
        await deps.controller_service.close_encashment(dto)

        with pytest.raises(EncashmentNotFoundError):
            not_found_dto = dto.model_copy(update={"encashment_id": uuid.uuid4()})
            await deps.controller_service.close_encashment(not_found_dto)

        with pytest.raises(EncashmentAlreadyClosedError):
            await deps.controller_service.close_encashment(dto)

    except Exception as e:
        assert error == e
    else:
        await deps.db_session.refresh(encashment)
        assert encashment.is_closed
        assert encashment.received_amount == 90
