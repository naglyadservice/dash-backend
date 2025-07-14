from dataclasses import dataclass
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Depends

from dash.infrastructure.s3 import S3UploadError
from dash.presentation.bearer import bearer_scheme
from dash.presentation.response_builder import build_responses
from dash.services.common.errors.company import CompanyNotFoundError
from dash.services.common.errors.location import LocationNotFoundError
from dash.services.common.errors.user import UserNotFoundError
from dash.services.company.dto import (
    CreateCompanyRequest,
    CreateCompanyResponse,
    DeleteLogoRequest,
    EditCompanyDTO,
    EditCompanyRequest,
    PublicCompanyScheme,
    ReadCompanyListResponse,
    ReadCompanyPublicRequest,
    UploadLogoRequest,
    UploadLogoResponse,
)
from dash.services.company.service import CompanyService
from dash.services.location.dto import AttachLocationToCompanyRequest
from dash.services.location.service import LocationService

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


@company_router.get("/{company_id}")
async def read_company_public(
    service: FromDishka[CompanyService],
    data: ReadCompanyPublicRequest = Depends(),
) -> PublicCompanyScheme:
    return await service.read_public_company(data)


@company_router.post(
    "",
    responses=build_responses(
        (404, (UserNotFoundError,)),
    ),
)
async def create_company(
    service: FromDishka[CompanyService], data: CreateCompanyRequest
) -> CreateCompanyResponse:
    return await service.create_company(data)


@company_router.patch(
    "/{company_id}",
    status_code=204,
    responses=build_responses(
        (404, (UserNotFoundError,)),
    ),
)
async def edit_company(
    service: FromDishka[CompanyService], company_id: UUID, data: EditCompanyDTO
) -> None:
    await service.edit_company(EditCompanyRequest(company_id=company_id, data=data))


@company_router.post(
    "/{company_id}/logo", responses=build_responses((503, (S3UploadError,)))
)
async def upload_logo(
    service: FromDishka[CompanyService], data: UploadLogoRequest = Depends()
) -> UploadLogoResponse:
    return await service.upload_logo(data)


@company_router.delete(
    "/{company_id}/logo",
    status_code=204,
    responses=build_responses((503, (S3UploadError,))),
)
async def delete_logo(
    service: FromDishka[CompanyService], data: DeleteLogoRequest = Depends()
) -> None:
    await service.delete_logo(data)


@dataclass
class LocationIdDTO:
    location_id: UUID


@company_router.post(
    "/{company_id}/locations",
    responses=build_responses(
        (404, (CompanyNotFoundError, LocationNotFoundError)),
    ),
)
async def attach_location_to_company(
    service: FromDishka[LocationService], company_id: UUID, data: LocationIdDTO
) -> None:
    return await service.attach_location_to_company(
        AttachLocationToCompanyRequest(
            location_id=data.location_id, company_id=company_id
        )
    )
