from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.models.admin_user import AdminRole, AdminUser
from dash.models.company import Company
from dash.models.location import Location


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
        db_session.add(self.company_owner)
        await db_session.flush()

        self.company = Company(
            name="Test Company",
            owner_id=self.company_owner.id,
        )
        db_session.add(self.company)
        await db_session.flush()

        self.location = Location(
            name="Test Location",
            address="Test Address",
            company_id=self.company.id,
        )

        self.location_admin = AdminUser(
            name="Test Location Admin",
            email="test_location_admin@test.com",
            password_hash="test",
            role=AdminRole.LOCATION_ADMIN,
        )

        db_session.add_all(
            (
                self.superadmin,
                self.location,
                self.location_admin,
            )
        )
        await db_session.commit()
