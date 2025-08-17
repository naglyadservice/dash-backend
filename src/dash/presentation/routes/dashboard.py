from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.presentation.bearer import bearer_scheme
from dash.services.dashboard.dto import (
    ReadDashboardStatsRequest,
    ReadDashboardStatsResponse,
)
from dash.services.dashboard.service import DashboardService

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["DASHBOARD"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@dashboard_router.get("")
async def read_dashboard_stats(
    dashboard_service: FromDishka[DashboardService],
    data: ReadDashboardStatsRequest = Depends(),
) -> ReadDashboardStatsResponse:
    return await dashboard_service.read_dashboard_stats(data)
