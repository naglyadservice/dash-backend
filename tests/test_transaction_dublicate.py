from datetime import datetime

import pytest
from dishka import AsyncContainer

from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.models import TransactionType, WsmTransaction
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


def create_transaction(test_env: TestEnvironment):
    return WsmTransaction(
        controller_transaction_id=123,
        controller_id=test_env.controller_1.id,
        location_id=test_env.location_1.id,
        coin_amount=100,
        bill_amount=200,
        prev_amount=300,
        free_amount=400,
        qr_amount=500,
        paypass_amount=600,
        type=TransactionType.WATER_VENDING.value,
        created_at_controller=datetime(2020, 1, 1),
        out_liters_1=1000,
        out_liters_2=2000,
        sale_type="test",
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_transaction_dublicate(
    request_di_container: AsyncContainer, test_env: TestEnvironment
):
    transaction_repository = await request_di_container.get(TransactionRepository)

    transaction = create_transaction(test_env)
    was_inserted = await transaction_repository.insert_with_conflict_ignore(transaction)
    assert was_inserted

    transaction = create_transaction(test_env)
    was_inserted = await transaction_repository.insert_with_conflict_ignore(transaction)
    assert not was_inserted
