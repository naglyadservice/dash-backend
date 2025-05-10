from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

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

        self.company_owner = AdminUser(
            name="Test Company Owner",
            email="test_company_owner@test.com",
            password_hash="test",
            role=AdminRole.COMPANY_OWNER,
        )

        self.company_owner_1 = AdminUser(
            name="Test Company Owner 1",
            email="test_company_owner_1@test.com",
            password_hash="test",
            role=AdminRole.COMPANY_OWNER,
        )

        db_session.add_all((self.company_owner, self.company_owner_1))
        await db_session.flush()

        self.company = Company(
            name="Test Company",
            owner_id=self.company_owner.id,
        )

        self.company_1 = Company(
            name="Test Company 1",
            owner_id=self.company_owner_1.id,
        )

        db_session.add_all((self.company, self.company_1))
        await db_session.flush()

        self.location = Location(
            name="Test Location",
            address="Test Address",
            company_id=self.company.id,
        )

        self.location_1 = Location(
            name="Test Location 1",
            address="Test Address 1",
            company_id=self.company_1.id,
        )

        self.location_admin = AdminUser(
            name="Test Location Admin",
            email="test_location_admin@test.com",
            password_hash="test",
            role=AdminRole.LOCATION_ADMIN,
        )

        self.location_admin_1 = AdminUser(
            name="Test Location Admin 1",
            email="test_location_admin_1@test.com",
            password_hash="test",
            role=AdminRole.LOCATION_ADMIN,
        )

        db_session.add_all(
            (self.location, self.location_1, self.location_admin, self.location_admin_1)
        )
        await db_session.flush()

        self.controller = WaterVendingController(
            name="Test Controller",
            device_id="test_device_id",
            location_id=self.location.id,
            type=ControllerType.WATER_VENDING,
            version="1.0.0",
            status=ControllerStatus.ACTIVE,
        )

        db_session.add_all(
            (
                self.superadmin,
                self.controller,
                LocationAdmin(
                    location_id=self.location.id, user_id=self.location_admin.id
                ),
                LocationAdmin(
                    location_id=self.location_1.id, user_id=self.location_admin_1.id
                ),
            )
        )
        await db_session.commit()
