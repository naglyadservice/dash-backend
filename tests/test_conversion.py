import pytest

from dash.services.controller.dto import PublicCarwashScheme, PublicWsmScheme
from dash.services.iot.carwash.dto import CarwashIoTControllerScheme
from dash.services.iot.wsm.dto import WsmIoTControllerScheme
from tests.context.settings import carwash_state, mock_energy_state, wsm_state
from tests.environment import TestEnvironment

pytestmark = pytest.mark.usefixtures("create_tables")


@pytest.mark.asyncio(loop_scope="session")
async def test_public_scheme(test_env: TestEnvironment):
    PublicWsmScheme.model_validate(test_env.controller_1)
    PublicCarwashScheme.model_validate(test_env.controller_2)


@pytest.mark.asyncio(loop_scope="session")
async def test_iot_scheme(test_env: TestEnvironment):
    WsmIoTControllerScheme.make(test_env.controller_1, wsm_state, mock_energy_state)
    CarwashIoTControllerScheme.make(
        test_env.controller_2, carwash_state, mock_energy_state
    )
