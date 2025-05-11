from decimal import Decimal

from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.models import Customer
from dash.models.admin_user import AdminRole, AdminUser
from dash.models.company import Company
from dash.models.controllers.controller import ControllerStatus, ControllerType
from dash.models.controllers.water_vending import WaterVendingController
from dash.models.location import Location
from dash.models.location_admin import LocationAdmin


class TestEnvironment:
    __test__ = False

    async def create_test_env(self, request_di_container: AsyncContainer):
        db_session = await request_di_container.get(AsyncSession)

        self.superadmin = AdminUser(
            name="Test Superadmin",
            email="test_superadmin@test.com",
            password_hash="test",
            role=AdminRole.SUPERADMIN,
        )

        self.company_owner_1 = AdminUser(
            name="Test Company Owner",
            email="test_company_owner@test.com",
            password_hash="test",
            role=AdminRole.COMPANY_OWNER,
        )

        self.company_owner_2 = AdminUser(
            name="Test Company Owner 1",
            email="test_company_owner_1@test.com",
            password_hash="test",
            role=AdminRole.COMPANY_OWNER,
        )

        db_session.add_all((self.company_owner_1, self.company_owner_2))
        await db_session.flush()

        self.company_1 = Company(
            name="Test Company 1",
            owner_id=self.company_owner_1.id,
        )

        self.company_2 = Company(
            name="Test Company 2",
            owner_id=self.company_owner_2.id,
        )

        db_session.add_all((self.company_1, self.company_2))
        await db_session.flush()

        self.location_1 = Location(
            name="Test Location 1",
            address="Test Address 1",
            company_id=self.company_1.id,
        )

        self.location_2 = Location(
            name="Test Location 2",
            address="Test Address 2",
            company_id=self.company_2.id,
        )

        self.location_admin_1 = AdminUser(
            name="Test Location Admin",
            email="test_location_admin_1@test.com",
            password_hash="test",
            role=AdminRole.LOCATION_ADMIN,
        )

        self.location_admin_2 = AdminUser(
            name="Test Location Admin 2",
            email="test_location_admin_2@test.com",
            password_hash="test",
            role=AdminRole.LOCATION_ADMIN,
        )

        db_session.add_all(
            (
                self.location_1,
                self.location_2,
                self.location_admin_1,
                self.location_admin_2,
            )
        )
        await db_session.flush()

        self.controller_1 = WaterVendingController(
            name="Test Controller 1",
            device_id="test_device_id_1",
            location_id=self.location_1.id,
            type=ControllerType.WATER_VENDING,
            version="1.0.0",
            status=ControllerStatus.ACTIVE,
        )

        self.customer = Customer(
            company_id=self.company_1.id,
            email="test_customer@test.com",
            name="Test Customer",
            card_id="test_card_id",
            balance=Decimal("100.00"),
        )

        db_session.add_all(
            (
                self.superadmin,
                self.controller_1,
                LocationAdmin(
                    location_id=self.location_1.id, user_id=self.location_admin_1.id
                ),
                LocationAdmin(
                    location_id=self.location_2.id, user_id=self.location_admin_2.id
                ),
                self.customer,
            )
        )
        await db_session.commit()
