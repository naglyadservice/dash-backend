from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.company import CompanyRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.s3 import S3Service
from dash.models.admin_user import AdminRole
from dash.models.company import Company
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.company import CompanyNotFoundError
from dash.services.common.errors.user import UserNotFoundError
from dash.services.company.dto import (
    CompanyScheme,
    CreateCompanyRequest,
    CreateCompanyResponse,
    EditCompanyRequest,
    PublicCompanyScheme,
    ReadCompanyListResponse,
    ReadCompanyPublicRequest,
    UploadLogoRequest,
    UploadLogoResponse,
)
from dash.services.user.service import UserService


class CompanyService:
    def __init__(
        self,
        company_repository: CompanyRepository,
        identity_provider: IdProvider,
        user_repository: UserRepository,
        user_service: UserService,
        s3_service: S3Service,
    ) -> None:
        self.company_repository = company_repository
        self.identity_provider = identity_provider
        self.user_repository = user_repository
        self.user_service = user_service
        self.s3_service = s3_service

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
            offer_agreement=data.offer_agreement,
            privacy_policy=data.privacy_policy,
            about=data.about,
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
            raise AccessForbiddenError

        return ReadCompanyListResponse(
            companies=[
                CompanyScheme.model_validate(company, from_attributes=True)
                for company in companies
            ]
        )

    async def edit_company(self, data: EditCompanyRequest) -> None:
        await self.identity_provider.ensure_company_owner(data.company_id)
        company = await self.company_repository.get(data.company_id)

        if not company:
            raise CompanyNotFoundError

        dict_data = data.data.model_dump(exclude_unset=True)
        for k, v in dict_data.items():
            if hasattr(company, k):
                setattr(company, k, v)

        await self.company_repository.commit()

    async def upload_logo(self, data: UploadLogoRequest) -> UploadLogoResponse:
        await self.identity_provider.ensure_company_owner(data.company_id)

        company = await self.company_repository.get(data.company_id)
        if not company:
            raise CompanyNotFoundError

        logo_key = f"companies/{data.company_id}/logo.png"
        await self.s3_service.upload_file(data.file.file, logo_key)

        company.logo_key = logo_key
        await self.company_repository.commit()

        return UploadLogoResponse(logo_key=logo_key)

    async def read_public_company(self, data: ReadCompanyPublicRequest):
        await self.identity_provider.authorize_customer()

        company = await self.company_repository.get(data.company_id)

        if not company:
            raise CompanyNotFoundError

        return PublicCompanyScheme.model_validate(company)
