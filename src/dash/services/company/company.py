from dash.infrastructure.auth.errors import UserNotFoundError
from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.company import CompanyRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.models.admin_user import AdminRole
from dash.models.company import Company
from dash.services.common.errors.base import AccessDeniedError
from dash.services.company.dto import (
    CompanyScheme,
    CreateCompanyRequest,
    CreateCompanyResponse,
    ReadCompanyListResponse,
)
from dash.services.user.user import UserService


class CompanyService:
    def __init__(
        self,
        company_repository: CompanyRepository,
        identity_provider: IdProvider,
        user_repository: UserRepository,
        user_service: UserService,
    ) -> None:
        self.company_repository = company_repository
        self.identity_provider = identity_provider
        self.user_repository = user_repository
        self.user_service = user_service

    async def create_company(self, data: CreateCompanyRequest) -> CreateCompanyResponse:
        await self.identity_provider.ensure_superadmin()

        owner_id = data.owner_id
        new_owner = None

        if data.owner_id is not None:
            if not await self.user_repository.exists_by_id(data.owner_id):
                raise UserNotFoundError

        elif data.new_owner is not None:
            new_owner = await self.user_service.create_company_owner(data.new_owner)
            owner_id = new_owner.id

        company = Company(
            name=data.name,
            owner_id=owner_id,
        )
        self.company_repository.add(company)
        await self.company_repository.commit()

        return CreateCompanyResponse(company_id=company.id, created_owner=new_owner)

    async def read_companies(self) -> ReadCompanyListResponse:
        user = await self.identity_provider.authorize()

        if user.role is AdminRole.SUPERADMIN:
            companies = await self.company_repository.get_list_all()
        elif user.role is AdminRole.COMPANY_OWNER:
            companies = await self.company_repository.get_list_by_owner(user.id)
        else:
            raise AccessDeniedError

        return ReadCompanyListResponse(
            companies=[
                CompanyScheme.model_validate(company, from_attributes=True)
                for company in companies
            ]
        )
