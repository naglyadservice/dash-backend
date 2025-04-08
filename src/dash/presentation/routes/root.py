from fastapi import APIRouter

from dash.presentation.routes.acquiring import acquiring_router
from dash.presentation.routes.auth import auth_router
from dash.presentation.routes.controller import controller_router
from dash.presentation.routes.location import location_router
from dash.presentation.routes.payment import payment_router
from dash.presentation.routes.transaction import transaction_router
from dash.presentation.routes.user import user_router
from dash.presentation.routes.water_vending import water_vending_router

root_router = APIRouter(prefix="/api")
root_router.include_router(acquiring_router)
root_router.include_router(auth_router)
root_router.include_router(water_vending_router)
root_router.include_router(transaction_router)
root_router.include_router(payment_router)
root_router.include_router(controller_router)
root_router.include_router(user_router)
root_router.include_router(location_router)


@root_router.get("/health")
async def health():
    return {"status": "ok"}
