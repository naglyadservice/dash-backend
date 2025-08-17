from contextlib import asynccontextmanager

from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from dash.infrastructure.iot.carwash.client import CarwashIoTClient
from dash.infrastructure.iot.fiscalizer.client import FiscalizerIoTClient
from dash.infrastructure.iot.laundry.client import LaundryIoTClient
from dash.infrastructure.iot.mqtt.client import MqttClient
from dash.infrastructure.iot.wsm.client import WsmIoTClient
from dash.main.config import Config
from dash.main.di import setup_di
from dash.main.logging.access import access_logs_middleware
from dash.presentation.exception_handlers import setup_exception_handlers
from dash.presentation.routes.root import root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    di_container: AsyncContainer = app.state.dishka_container
    await di_container.get(WsmIoTClient)
    await di_container.get(CarwashIoTClient)
    await di_container.get(FiscalizerIoTClient)
    await di_container.get(MqttClient)
    await di_container.get(LaundryIoTClient)

    yield

    await di_container.close()


def get_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(root_router)

    config = Config()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.app.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(BaseHTTPMiddleware, dispatch=access_logs_middleware)

    setup_exception_handlers(app)
    setup_dishka(container=setup_di(config), app=app)

    return app
