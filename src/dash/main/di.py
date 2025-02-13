from dishka import AsyncContainer, Provider, Scope, make_async_container
from fastapi import Request

from dash.infrastructure.auth.auth_service import AuthService
from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.db.setup import (
    get_async_engine,
    get_async_session,
    get_async_sessionmaker,
)
from dash.infrastructure.db.tracker import SATracker
from dash.infrastructure.db.transaction_manager import SATransactionManager
from dash.infrastructure.gateways.user_gateway import UserMapper
from dash.infrastructure.storages.redis import get_redis_client, get_redis_pool
from dash.infrastructure.storages.session import SessionStorage
from dash.main.config import AppConfig, Config, DbConfig, RedisConfig


def provide_configs() -> Provider:
    provider = Provider()
    config = Config()

    provider.provide(lambda: config.db, provides=DbConfig, scope=Scope.APP)
    provider.provide(lambda: config.redis, provides=RedisConfig, scope=Scope.APP)
    provider.provide(lambda: config.app, provides=AppConfig, scope=Scope.APP)

    return provider


def provide_db() -> Provider:
    provider = Provider()

    provider.provide(get_async_engine, scope=Scope.APP)
    provider.provide(get_async_sessionmaker, scope=Scope.APP)
    provider.provide(get_async_session, scope=Scope.REQUEST)

    provider.provide(SATransactionManager, scope=Scope.REQUEST)
    provider.provide(SATracker, scope=Scope.REQUEST)

    provider.provide(get_redis_pool, scope=Scope.APP)
    provider.provide(get_redis_client, scope=Scope.REQUEST)

    provider.provide(SessionStorage, scope=Scope.REQUEST)

    return provider


def provide_gateways() -> Provider:
    provider = Provider()

    provider.provide(UserMapper, scope=Scope.REQUEST)

    return provider


def provide_infrastructure() -> Provider:
    provider = Provider()

    provider.from_context(Request, scope=Scope.REQUEST)

    provider.provide(PasswordProcessor, scope=Scope.REQUEST)
    provider.provide(AuthService, scope=Scope.REQUEST)
    provider.provide(IdProvider, scope=Scope.REQUEST)

    return provider


def setup_di() -> AsyncContainer:
    return make_async_container(
        provide_configs(),
        provide_db(),
        provide_gateways(),
        provide_infrastructure(),
    )
