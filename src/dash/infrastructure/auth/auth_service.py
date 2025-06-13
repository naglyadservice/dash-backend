import secrets
import string

from dash.infrastructure.auth.dto import (
    CompleteCustomerRegistrationRequest,
    CompletePasswordResetRequest,
    CustomerRegistrationResponse,
    LoginCustomerRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterCustomerRequest,
    StartPasswordResetRequest,
)
from dash.infrastructure.auth.errors import (
    InvalidCredentialsError,
    InvalidVerificationCodeError,
)
from dash.infrastructure.auth.password_processor import PasswordProcessor
from dash.infrastructure.auth.sms_sender import SMSClient
from dash.infrastructure.auth.token_processor import JWTTokenProcessor
from dash.infrastructure.repositories.company import CompanyRepository
from dash.infrastructure.repositories.customer import CustomerRepository
from dash.infrastructure.repositories.user import UserRepository
from dash.infrastructure.storages.session import SessionStorage
from dash.infrastructure.storages.verification import VerificationStorage
from dash.models.customer import Customer
from dash.services.common.errors.company import CompanyNotFoundError
from dash.services.common.errors.user import (
    CustomerNotFoundError,
    PhoneNumberAlreadyTakenError,
)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        customer_repository: CustomerRepository,
        company_repository: CompanyRepository,
        verification_storage: VerificationStorage,
        password_processor: PasswordProcessor,
        session_storage: SessionStorage,
        token_processor: JWTTokenProcessor,
        sms_client: SMSClient,
    ) -> None:
        self.user_repository = user_repository
        self.customer_repository = customer_repository
        self.company_repository = company_repository
        self.verification_storage = verification_storage
        self.password_processor = password_processor
        self.session_storage = session_storage
        self.token_processor = token_processor
        self.sms_client = sms_client

    async def authenticate(self, data: LoginRequest) -> LoginResponse:
        user = await self.user_repository.get_by_email(data.email)
        if not user:
            raise InvalidCredentialsError

        if not self.password_processor.verify(data.password, user.password_hash):
            raise InvalidCredentialsError

        return LoginResponse(
            access_token=self.token_processor.create_access_token(user.id),
            refresh_token=self.token_processor.create_refresh_token(user.id),
        )

    async def authenticate_customer(self, data: LoginCustomerRequest) -> LoginResponse:
        customer = await self.customer_repository.get_by_phone(
            data.company_id, data.phone_number
        )
        if not customer:
            raise InvalidCredentialsError

        if not self.password_processor.verify(
            data.password, customer.password_hash or ""
        ):
            raise InvalidCredentialsError

        return LoginResponse(
            access_token=self.token_processor.create_access_token(customer.id),
            refresh_token=self.token_processor.create_refresh_token(customer.id),
        )

    async def refresh_token(self, data: RefreshTokenRequest) -> RefreshTokenResponse:
        user_id = self.token_processor.validate_refresh_token(data.refresh_token)
        return RefreshTokenResponse(
            access_token=self.token_processor.create_access_token(user_id),
        )

    async def logout(self, data: LogoutRequest) -> None:
        await self.session_storage.add_blacklist(data.access_token)

    async def start_customer_registration(self, data: RegisterCustomerRequest) -> None:
        if not await self.company_repository.exists(data.company_id):
            raise CompanyNotFoundError

        if await self.customer_repository.exists(data.company_id, data.phone_number):
            raise PhoneNumberAlreadyTakenError

        code = self._generate_code()
        while await self.verification_storage.registration_code_exists(code):
            code = self._generate_code()

        await self.sms_client.send_sms(
            recipients=[data.phone_number],
            message=f"Код для верифікації: {code}. Якщо ви не запрошували код, проігноруйте це SMS повідомлення.",
        )

        await self.verification_storage.set_registration_code(
            code=code,
            data=data,
            ttl=300,
        )

    async def complete_customer_registration(
        self, data: CompleteCustomerRegistrationRequest
    ) -> CustomerRegistrationResponse:
        user_data = await self.verification_storage.verify_registration_code(data.code)
        if user_data is None:
            raise InvalidVerificationCodeError

        if await self.customer_repository.exists(
            user_data.company_id, user_data.phone_number
        ):
            raise PhoneNumberAlreadyTakenError

        customer = Customer(
            company_id=user_data.company_id,
            phone_number=user_data.phone_number,
            password_hash=self.password_processor.hash(user_data.password),
        )

        self.customer_repository.add(customer)
        await self.customer_repository.commit()

        await self.verification_storage.delete_registration_code(data.code)

        return CustomerRegistrationResponse(
            access_token=self.token_processor.create_access_token(customer.id),
            refresh_token=self.token_processor.create_refresh_token(customer.id),
        )

    def _generate_code(self) -> str:
        return "".join(secrets.choice(string.digits) for _ in range(4))

    async def start_password_reset(self, data: StartPasswordResetRequest) -> None:
        if not await self.customer_repository.exists(
            data.company_id, data.phone_number
        ):
            raise CustomerNotFoundError

        code = self._generate_code()

        await self.sms_client.send_sms(
            recipients=[data.phone_number],
            message=f"Код для зміни паролю: {code}.",
        )

        await self.verification_storage.set_reset_code(
            code=code,
            data=data,
            ttl=300,
        )

    async def complete_password_reset(self, data: CompletePasswordResetRequest) -> None:
        stored_data = await self.verification_storage.verify_reset_code(data.code)

        if stored_data is None:
            raise InvalidVerificationCodeError

        customer = await self.customer_repository.get_by_phone(
            company_id=stored_data.company_id,
            phone_number=stored_data.phone_number,
        )

        if not customer:
            raise CustomerNotFoundError

        customer.password_hash = self.password_processor.hash(data.new_password)

        await self.customer_repository.commit()

        await self.verification_storage.delete_reset_code(data.code)
