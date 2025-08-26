import pytest

from dash.services.controller.dto import (
    PublicCarCleanerScheme,
    PublicCarwashScheme,
    PublicVacuumScheme,
    PublicWsmScheme,
)
from dash.services.iot.car_cleaner.dto import CarCleanerIoTControllerScheme
from dash.services.iot.carwash.dto import CarwashIoTControllerScheme
from dash.services.iot.fiscalizer.dto import FiscalizerIoTControllerScheme
from dash.services.iot.laundry.dto import LaundryIoTControllerScheme
from dash.services.iot.wsm.dto import WsmIoTControllerScheme
from tests.context.settings import (
    car_cleaner_state,
    carwash_state,
    fiscalizer_state,
    laundry_state,
    mock_energy_state,
    wsm_state,
)
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@pytest.mark.asyncio(loop_scope="session")
async def test_public_scheme(test_env: TestEnvironment):
    PublicWsmScheme.model_validate(test_env.controller_1)
    PublicCarwashScheme.model_validate(test_env.controller_2)
    PublicCarCleanerScheme.model_validate(test_env.controller_4)
    PublicVacuumScheme.model_validate(test_env.controller_5)


@pytest.mark.asyncio(loop_scope="session")
async def test_iot_scheme(test_env: TestEnvironment):
    WsmIoTControllerScheme.make(
        test_env.controller_1, wsm_state, mock_energy_state, True
    )
    CarwashIoTControllerScheme.make(
        test_env.controller_2, carwash_state, mock_energy_state, False
    )
    FiscalizerIoTControllerScheme.make(
        test_env.controller_3, fiscalizer_state, mock_energy_state, True
    )
    CarCleanerIoTControllerScheme.make(
        test_env.controller_4, car_cleaner_state, mock_energy_state, True
    )
    LaundryIoTControllerScheme.make(
        test_env.laundry_controller_fixed, laundry_state, None, True
    )
