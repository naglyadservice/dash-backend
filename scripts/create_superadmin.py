import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.main.config import DbConfig
from dash.models.admin_user import AdminRole, AdminUser


async def create_superadmin() -> None:
    email = input("Enter email: ")
    password = input("Enter password: ")
    name = input("Enter name: ")

    config = DbConfig()
    engine = create_async_engine(config.build_dsn())
    session_maker = async_sessionmaker(engine)

    user = AdminUser(
        email=email,
        name=name,
        password_hash=PasswordProcessor().hash(password),
        role=AdminRole.SUPERADMIN,
    )

    async with session_maker() as session:
        session.add(user)
        await session.commit()

    print("Superadmin created successfully")


if __name__ == "__main__":
    asyncio.run(create_superadmin())
