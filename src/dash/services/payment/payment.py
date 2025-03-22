from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.payment import PaymentRepository
from dash.services.payment.dto import (
    PaymentScheme,
    ReadPaymentsRequest,
    ReadPaymentsResponse,
)


class PaymentService:
    def __init__(
        self, identity_provider: IdProvider, payment_repository: PaymentRepository
    ):
        self.identity_provider = identity_provider
        self.payment_repository = payment_repository

    async def read_payments(self, data: ReadPaymentsRequest) -> ReadPaymentsResponse:
        await self.identity_provider.ensure_admin()

        payments, total = await self.payment_repository.get_list(data)

        return ReadPaymentsResponse(
            payments=[
                PaymentScheme.model_validate(payment, from_attributes=True)
                for payment in payments
            ],
            total=total,
        )
