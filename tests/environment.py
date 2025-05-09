from dishka import AsyncContainer
from sqlalchemy.ext.asyncio import AsyncSession

from dash.models.company import Company
from dash.models.location import Location
from dash.models.user import User, UserRole


class TestEnvironment:
    __test__ = False

    async def create_test_env(self, request_di_container: AsyncContainer):
        db_session = await request_di_container.get(AsyncSession)

        self.superadmin = User(
            name="Test Superadmin",
            email="test_superadmin@test.com",
            password_hash="test",
            role=UserRole.SUPERADMIN,
        )

        self.company_owner = User(
            name="Test Company Owner",
            email="test_company_owner@test.com",
            password_hash="test",
            role=UserRole.COMPANY_OWNER,
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

        self.location_admin = User(
            name="Test Location Admin",
            email="test_location_admin@test.com",
            password_hash="test",
            role=UserRole.LOCATION_ADMIN,
        )

        db_session.add_all(
            (
                self.superadmin,
                self.location,
                self.location_admin,
            )
        )
        await db_session.commit()
