from typing import Sequence

from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.models.admin_user import AdminRole, AdminUser
from dash.models.customer import Customer
from dash.services.common.errors.base import AccessForbiddenError
from dash.services.common.errors.user import (
    CardIdAlreadyTakenError,
    CustomerNotFoundError,
    EmailAlreadyTakenError,
    InvalidCurrentPasswordError,
)
from dash.services.customer.dto import (
    ChangeCustomerPasswordRequest,
    CreateCustomerRequest,
    CreateCustomerResponse,
    CustomerProfileResponse,
    CustomerScheme,
    DeleteCustomerRequest,
    EditCustomerRequest,
    ReadCustomerListRequest,
    ReadCustomerListResponse,
    UpdateCustomerProfileRequest,
)


class CustomerService:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        identity_provider: IdProvider,
        password_processor: PasswordProcessor,
    ) -> None:
        self.customer_repository = customer_repository
        self.identity_provider = identity_provider
        self.password_processor = password_processor

    async def _get_customers_by_role(
        self, data: ReadCustomerListRequest, user: AdminUser
    ) -> tuple[Sequence[Customer], int]:
        match user.role:
            case AdminRole.SUPERADMIN:
                return await self.customer_repository.get_list_all(data)
            case AdminRole.COMPANY_OWNER:
                return await self.customer_repository.get_list_by_owner(data, user.id)
            case AdminRole.LOCATION_ADMIN:
                return await self.customer_repository.get_list_by_admin(
                    data,
                    user.company_id,  # type: ignore
                )
            case _:
                raise AccessForbiddenError

    async def read_customers(
        self, data: ReadCustomerListRequest
    ) -> ReadCustomerListResponse:
        user = await self.identity_provider.authorize()

        if data.company_id is not None:
            if (
                user.company_id != data.company_id
                and user.role is not AdminRole.SUPERADMIN
            ):
                await self.identity_provider.ensure_company_owner(data.company_id)
            customers, total = await self.customer_repository.get_list_all(data)
        else:
            customers, total = await self._get_customers_by_role(data, user)

        return ReadCustomerListResponse(
            customers=[
                CustomerScheme.model_validate(customer) for customer in customers
            ],
            total=total,
        )

    async def create_customer(
        self, data: CreateCustomerRequest
    ) -> CreateCustomerResponse:
        user = await self.identity_provider.authorize()

        if user.role is AdminRole.LOCATION_ADMIN:
            if user.company_id != data.company_id:
                raise AccessForbiddenError
        else:
            await self.identity_provider.ensure_company_owner(data.company_id)

        if data.phone_number is not None:
            if await self.customer_repository.exists(
                data.company_id, data.phone_number
            ):
                raise EmailAlreadyTakenError

        if data.card_id is not None:
            if await self.customer_repository.exists_by_card_id(
                data.company_id, data.card_id
            ):
                raise CardIdAlreadyTakenError

        customer = Customer(**data.model_dump())

        self.customer_repository.add(customer)
        await self.customer_repository.commit()

        return CreateCustomerResponse(id=customer.id)

    async def edit_customer(self, data: EditCustomerRequest) -> None:
        customer = await self.customer_repository.get(data.id)
        if not customer:
            raise CustomerNotFoundError

        user = await self.identity_provider.authorize()
        if (
            not user.company_id == customer.company_id
            and user.role is AdminRole.LOCATION_ADMIN
        ):
            await self.identity_provider.ensure_company_owner(customer.company_id)

        dict_data = data.user.model_dump(exclude_unset=True)

        for key, value in dict_data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)

        await self.customer_repository.commit()

    async def delete_customer(self, data: DeleteCustomerRequest) -> None:
        customer = await self.customer_repository.get(data.id)
        if not customer:
            raise CustomerNotFoundError

        await self.identity_provider.ensure_company_owner(customer.company_id)

        await self.customer_repository.delete(customer)
        await self.customer_repository.commit()

    async def change_password(self, data: ChangeCustomerPasswordRequest) -> None:
        customer = await self.identity_provider.authorize_customer()

        if not customer.password_hash or not self.password_processor.verify(
            data.current_password, customer.password_hash
        ):
            raise InvalidCurrentPasswordError

        customer.password_hash = self.password_processor.hash(data.new_password)
        await self.customer_repository.commit()

    async def read_profile(self) -> CustomerProfileResponse:
        customer = await self.identity_provider.authorize_customer()
        return CustomerProfileResponse.model_validate(customer)

    async def update_profile(self, data: UpdateCustomerProfileRequest) -> None:
        customer = await self.identity_provider.authorize_customer()
        if data.name is not None:
            customer.name = data.name
        if data.birth_date is not None:
            customer.birth_date = data.birth_date
        await self.customer_repository.commit()
