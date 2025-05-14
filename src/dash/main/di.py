from dishka import AnyOf, AsyncContainer, Provider, Scope, make_async_container
from fastapi import Request
from npc_iot import NpcClient as NpcIotClient

from dash.infrastructure.acquring.liqpay import LiqpayService
from dash.infrastructure.acquring.monopay import MonopayService
from dash.infrastructure.auth.auth_service import AuthService
from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.auth.token_processor import JWTTokenProcessor
from dash.infrastructure.db.setup import (
    get_async_engine,
    get_async_session,
    get_async_sessionmaker,
)
from dash.infrastructure.iot.wsm.di import WsmClient, get_npc_client
from dash.infrastructure.repositories.company import CompanyRepository
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.storages.acquring import AcquringStorage
from dash.infrastructure.storages.iot import IotStorage
from dash.infrastructure.storages.redis import get_redis_client, get_redis_pool
from dash.infrastructure.storages.session import SessionStorage
from dash.main.config import (
    AppConfig,
    Config,
    DbConfig,
    JWTConfig,
    LiqpayConfig,
    MonopayConfig,
    MqttConfig,
    RedisConfig,
)
from dash.services.company.company import CompanyService
from dash.services.controller.controller import ControllerService
from dash.services.customer.customer import CustomerService
from dash.services.location.location import LocationService
from dash.services.payment.payment import PaymentService
from dash.services.transaction.transaction import TransactionService
from dash.services.user.user import UserService
from dash.services.water_vending.water_vending import WaterVendingService


def provide_configs() -> Provider:
    provider = Provider(scope=Scope.APP)

    provider.from_context(Config, scope=Scope.APP)
    provider.from_context(DbConfig, scope=Scope.APP)
    provider.from_context(RedisConfig, scope=Scope.APP)
    provider.from_context(AppConfig, scope=Scope.APP)
    provider.from_context(MqttConfig, scope=Scope.APP)
    provider.from_context(MonopayConfig, scope=Scope.APP)
    provider.from_context(LiqpayConfig, scope=Scope.APP)
    provider.from_context(JWTConfig, scope=Scope.APP)

    return provider


def provide_db() -> Provider:
    provider = Provider()

    provider.provide(get_async_engine, scope=Scope.APP)
    provider.provide(get_async_sessionmaker, scope=Scope.APP)
    provider.provide(get_async_session, scope=Scope.REQUEST)

    provider.provide(get_redis_pool, scope=Scope.APP)
    provider.provide(get_redis_client, scope=Scope.REQUEST)

    return provider


def provide_services() -> Provider:
    provider = Provider(scope=Scope.REQUEST)

    provider.provide_all(
        WaterVendingService,
        TransactionService,
        PaymentService,
        ControllerService,
        LocationService,
        UserService,
        CompanyService,
        CustomerService,
    )
    return provider


def provide_gateways() -> Provider:
    provider = Provider(scope=Scope.REQUEST)

    provider.provide_all(
        UserRepository,
        ControllerRepository,
        CustomerRepository,
        TransactionRepository,
        PaymentRepository,
        AcquringStorage,
        LocationRepository,
        SessionStorage,
        CompanyRepository,
        IotStorage,
    )
    return provider


def provide_infrastructure() -> Provider:
    provider = Provider()

    provider.from_context(Request, scope=Scope.REQUEST)

    provider.provide(PasswordProcessor, scope=Scope.REQUEST)
    provider.provide(JWTTokenProcessor, scope=Scope.REQUEST)
    provider.provide(AuthService, scope=Scope.REQUEST)
    provider.provide(IdProvider, scope=Scope.REQUEST)

    provider.provide(
        get_npc_client, scope=Scope.APP, provides=AnyOf[WsmClient, NpcIotClient]
    )
    provider.provide(MonopayService, scope=Scope.REQUEST)
    provider.provide(LiqpayService, scope=Scope.REQUEST)

    return provider


def get_providers() -> tuple[Provider, ...]:
    return (
        provide_configs(),
        provide_db(),
        provide_gateways(),
        provide_infrastructure(),
        provide_services(),
    )


def setup_di(config: Config) -> AsyncContainer:
    return make_async_container(
        *get_providers(),
        context={
            Config: config,
            DbConfig: config.db,
            RedisConfig: config.redis,
            AppConfig: config.app,
            MqttConfig: config.mqtt,
            MonopayConfig: config.monopay,
            LiqpayConfig: config.liqpay,
            JWTConfig: config.jwt,
        },
    )
