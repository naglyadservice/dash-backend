from contextlib import asynccontextmanager

import uvicorn
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from dash.infrastructure.mqtt.client import NpcClient
from dash.main.config import Config
from dash.main.di import setup_di
from dash.main.logging.access import access_logger
from dash.main.logging.setup import configure_logging
from dash.presentation.exception_handlers import setup_exception_handlers
from dash.presentation.routes.root import root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    di_container: AsyncContainer = app.state.dishka_container
    await di_container.get(NpcClient)

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
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(BaseHTTPMiddleware, dispatch=access_logger)

    setup_exception_handlers(app)
    setup_dishka(container=setup_di(config), app=app)

    return app


def run() -> None:
    config = Config()
    configure_logging(
        level=config.logging.level,
        json_logs=config.logging.json_mode,
        colorize=config.logging.colorize,
    )

    uvicorn.run(
        "dash.main.app:get_app",
        factory=True,
        host=config.app.host,
        port=config.app.port,
        reload=config.app.reload,
        access_log=False,
    )


if __name__ == "__main__":
    run()
