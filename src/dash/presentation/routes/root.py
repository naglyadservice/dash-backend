from typing import Literal

from fastapi import APIRouter

from dash.presentation.routes.auth import auth_router
from dash.presentation.routes.water_vending import water_vending_router

root_router = APIRouter(prefix="/api")
root_router.include_router(auth_router)
root_router.include_router(water_vending_router)


@root_router.get("/health", tags=["HEALTHCHECK"])
async def health() -> dict[Literal["status"], Literal["ok"]]:
    return {"status": "ok"}
