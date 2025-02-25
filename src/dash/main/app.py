import uvicorn
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from dash.main.config import AppConfig
from dash.main.di import setup_di
from dash.presentation.exception_handlers import setup_exception_handlers
from dash.presentation.routes.root import root_router


def get_app() -> FastAPI:
    app = FastAPI()
    app.include_router(root_router)

    setup_exception_handlers(app)
    setup_dishka(container=setup_di(), app=app)

    return app


def run() -> None:
    config = AppConfig()

    uvicorn.run(
        "dash.main.app:get_app",
        factory=True,
        host=config.host,
        port=config.port,
        reload=config.reload,
    )


if __name__ == "__main__":
    run()
