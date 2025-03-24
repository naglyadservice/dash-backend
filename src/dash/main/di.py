from typing import Any

from dishka import AnyOf, AsyncContainer, Provider, Scope, make_async_container
from fastapi import Request
from npc_iot import NpcClient as NpcIotClient

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
from dash.infrastructure.monopay import MonopayService
from dash.infrastructure.mqtt.client import NpcClient, get_npc_client
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.storages.acquring import AcquringStorage
from dash.infrastructure.storages.redis import get_redis_client, get_redis_pool
from dash.infrastructure.storages.session import SessionStorage
from dash.main.config import (
    AppConfig,
    Config,
    DbConfig,
    MonopayConfig,
    MqttConfig,
    RedisConfig,
)
from dash.services.controller.controller import ControllerService
from dash.services.payment.payment import PaymentService
from dash.services.transaction.transaction import TransactionService
from dash.services.water_vending.water_vending import WaterVendingService


def provide_configs(config: Config) -> Provider:
    provider = Provider()

    provider.provide(lambda: config.db, provides=DbConfig, scope=Scope.APP)
    provider.provide(lambda: config.redis, provides=RedisConfig, scope=Scope.APP)
    provider.provide(lambda: config.app, provides=AppConfig, scope=Scope.APP)
    provider.provide(lambda: config.mqtt, provides=MqttConfig, scope=Scope.APP)
    provider.provide(lambda: config.monopay, provides=MonopayConfig, scope=Scope.APP)

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

    return provider


def provide_services() -> Provider:
    provider = Provider()

    provider.provide(WaterVendingService, scope=Scope.REQUEST)
    provider.provide(TransactionService, scope=Scope.REQUEST)
    provider.provide(PaymentService, scope=Scope.REQUEST)
    provider.provide(ControllerService, scope=Scope.REQUEST)

    return provider


def provide_gateways() -> Provider:
    provider = Provider()

    provider.provide(SessionStorage, scope=Scope.REQUEST)

    provider.provide(UserRepository, scope=Scope.REQUEST)
    provider.provide(ControllerRepository, scope=Scope.REQUEST)
    provider.provide(TransactionRepository, scope=Scope.REQUEST)
    provider.provide(PaymentRepository, scope=Scope.REQUEST)
    provider.provide(AcquringStorage, scope=Scope.REQUEST)

    return provider


def provide_infrastructure() -> Provider:
    provider = Provider()

    provider.from_context(Request, scope=Scope.REQUEST)

    provider.provide(PasswordProcessor, scope=Scope.REQUEST)
    provider.provide(AuthService, scope=Scope.REQUEST)
    provider.provide(IdProvider, scope=Scope.REQUEST)

    provider.provide(
        get_npc_client, scope=Scope.APP, provides=AnyOf[NpcClient, NpcIotClient]
    )
    provider.provide(MonopayService, scope=Scope.REQUEST)

    return provider


def setup_di(config: Config) -> AsyncContainer:
    return make_async_container(
        provide_configs(config),
        provide_db(),
        provide_gateways(),
        provide_infrastructure(),
        provide_services(),
    )
