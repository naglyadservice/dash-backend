from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from dash.presentation.bearer import bearer_scheme
from dash.services.company.dto import (
    CreateCompanyRequest,
    CreateCompanyResponse,
    EditCompanyDTO,
    EditCompanyRequest,
    ReadCompanyListResponse,
)
from dash.services.company.service import CompanyService

company_router = APIRouter(
    prefix="/companies",
    tags=["COMPANIES"],
    route_class=DishkaRoute,
    dependencies=[bearer_scheme],
)


@company_router.get("")
async def read_companies(
    service: FromDishka[CompanyService],
) -> ReadCompanyListResponse:
    return await service.read_companies()


@company_router.post("")
async def create_company(
    service: FromDishka[CompanyService], data: CreateCompanyRequest
) -> CreateCompanyResponse:
    return await service.create_company(data)


@company_router.patch("/{company_id}", status_code=204)
async def edit_company(
    service: FromDishka[CompanyService], company_id: UUID, data: EditCompanyDTO
) -> None:
    await service.edit_company(EditCompanyRequest(company_id=company_id, data=data))
