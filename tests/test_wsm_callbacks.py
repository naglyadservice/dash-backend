from dataclasses import dataclass

import pytest
from dishka import AsyncContainer

from dash.infrastructure.repositories.company import CompanyRepository
from dash.presentation.callbacks_wsm.payment_card_get import payment_card_get_callback
from dash.services.company.company import CompanyService

pytestmark = pytest.mark.usefixtures("create_tables")


@dataclass
class CompanyDependencies:
    company_service: CompanyService
    company_repository: CompanyRepository


@pytest.fixture
async def deps(request_di_container: AsyncContainer):
    return CompanyDependencies(
        company_service=await request_di_container.get(CompanyService),
        company_repository=await request_di_container.get(CompanyRepository),
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_payment_card_get_callback(di_container: AsyncContainer):
    await payment_card_get_callback(
        "test_device_id",
        {"request_id": 1, "created": "test_created", "cardUID": "test_card_uid"},
        di_container=di_container,
    )
