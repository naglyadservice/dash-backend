from dishka import AsyncContainer, Provider, Scope, make_async_container
from fastapi import Request

from dash.infrastructure.acquiring.checkbox import CheckboxService
from dash.infrastructure.acquiring.liqpay import LiqpayGateway
from dash.infrastructure.acquiring.monopay import MonopayGateway
from dash.infrastructure.auth.auth_service import AuthService
from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.auth.sms_sender import SMSClient
from dash.infrastructure.auth.token_processor import JWTTokenProcessor
from dash.infrastructure.db.setup import (
    get_async_engine,
    get_async_session,
    get_async_sessionmaker,
)
from dash.infrastructure.iot.carwash.client import CarwashIoTClient
from dash.infrastructure.iot.carwash.di import get_carwash_client
from dash.infrastructure.iot.fiscalizer.client import FiscalizerIoTClient
from dash.infrastructure.iot.fiscalizer.di import get_fiscalizer_client
from dash.infrastructure.iot.laundry.client import LaundryIoTClient
from dash.infrastructure.iot.laundry.di import get_laundry_client
from dash.infrastructure.iot.mqtt.client import MqttClient
from dash.infrastructure.iot.mqtt.di import get_mqtt_client
from dash.infrastructure.iot.vacuum.client import VacuumIoTClient
from dash.infrastructure.iot.vacuum.di import get_vacuum_client
from dash.infrastructure.iot.wsm.client import WsmIoTClient
from dash.infrastructure.iot.wsm.di import get_wsm_client
from dash.infrastructure.repositories.company import CompanyRepository
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.repositories.encashment import EncashmentRepository
from dash.infrastructure.repositories.energy_state import EnergyStateRepository
from dash.infrastructure.repositories.location import LocationRepository
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.s3 import S3Service
from dash.infrastructure.storages.acquiring import AcquiringStorage
from dash.infrastructure.storages.carwash_session import CarwashSessionStorage
from dash.infrastructure.storages.iot import IoTStorage
from dash.infrastructure.storages.redis import get_redis_client, get_redis_pool
from dash.infrastructure.storages.session import SessionStorage
from dash.infrastructure.storages.verification import VerificationStorage
from dash.main.config import (
    AppConfig,
    Config,
    JWTConfig,
    LiqpayConfig,
    MonopayConfig,
    MqttConfig,
    PostgresConfig,
    RedisConfig,
    S3Config,
    SMSConfig,
)
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.common.payment_helper import PaymentHelper
from dash.services.company.service import CompanyService
from dash.services.controller.service import ControllerService
from dash.services.customer.service import CustomerService
from dash.services.dashboard.service import DashboardService
from dash.services.iot.carwash.customer_service import CustomerCarwashService
from dash.services.iot.carwash.service import CarwashService
from dash.services.iot.factory import IoTServiceFactory
from dash.services.iot.fiscalizer.service import FiscalizerService
from dash.services.iot.laundry.service import LaundryService
from dash.services.iot.vacuum.service import VacuumService
from dash.services.iot.wsm.service import WsmService
from dash.services.location.service import LocationService
from dash.services.payment.service import PaymentService
from dash.services.transaction.service import TransactionService
from dash.services.user.service import UserService


def provide_configs() -> Provider:
    provider = Provider(scope=Scope.APP)

    provider.from_context(Config, scope=Scope.APP)
    provider.from_context(PostgresConfig, scope=Scope.APP)
    provider.from_context(RedisConfig, scope=Scope.APP)
    provider.from_context(AppConfig, scope=Scope.APP)
    provider.from_context(MqttConfig, scope=Scope.APP)
    provider.from_context(MonopayConfig, scope=Scope.APP)
    provider.from_context(LiqpayConfig, scope=Scope.APP)
    provider.from_context(JWTConfig, scope=Scope.APP)
    provider.from_context(SMSConfig, scope=Scope.APP)
    provider.from_context(S3Config, scope=Scope.APP)

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
        WsmService,
        TransactionService,
        PaymentService,
        ControllerService,
        LocationService,
        UserService,
        CompanyService,
        CustomerService,
        CustomerCarwashService,
        CarwashService,
        FiscalizerService,
        LaundryService,
        VacuumService,
        IoTServiceFactory,
        CheckOnlineInteractor,
        PaymentHelper,
        DashboardService,
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
        AcquiringStorage,
        LocationRepository,
        SessionStorage,
        VerificationStorage,
        CompanyRepository,
        IoTStorage,
        CarwashSessionStorage,
        EncashmentRepository,
        EnergyStateRepository,
    )
    return provider


def provide_infrastructure() -> Provider:
    provider = Provider()

    provider.from_context(Request, scope=Scope.REQUEST)

    provider.provide(PasswordProcessor, scope=Scope.REQUEST)
    provider.provide(JWTTokenProcessor, scope=Scope.REQUEST)
    provider.provide(AuthService, scope=Scope.REQUEST)
    provider.provide(IdProvider, scope=Scope.REQUEST)

    provider.provide(get_wsm_client, scope=Scope.APP, provides=WsmIoTClient)
    provider.provide(get_carwash_client, scope=Scope.APP, provides=CarwashIoTClient)
    provider.provide(
        get_fiscalizer_client, scope=Scope.APP, provides=FiscalizerIoTClient
    )
    provider.provide(get_mqtt_client, scope=Scope.APP, provides=MqttClient)
    provider.provide(get_laundry_client, scope=Scope.APP, provides=LaundryIoTClient)
    provider.provide(get_vacuum_client, scope=Scope.APP, provides=VacuumIoTClient)

    provider.provide(LiqpayGateway, scope=Scope.REQUEST)
    provider.provide(MonopayGateway, scope=Scope.REQUEST)
    provider.provide(CheckboxService, scope=Scope.REQUEST)

    provider.provide(SMSClient, scope=Scope.REQUEST)
    provider.provide(S3Service, scope=Scope.REQUEST)

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
            PostgresConfig: config.postgres,
            RedisConfig: config.redis,
            AppConfig: config.app,
            MqttConfig: config.mqtt,
            MonopayConfig: config.monopay,
            LiqpayConfig: config.liqpay,
            JWTConfig: config.jwt,
            SMSConfig: config.sms,
            S3Config: config.s3,
        },
    )
