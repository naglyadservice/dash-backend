from dash.infrastructure.auth.id_provider import IdProvider
from dash.infrastructure.repositories.transaction import TransactionRepository
from dash.services.transaction.dto import (
    ReadTransactionsRequest,
    ReadTransactionsResponse,
    WaterVendingTransactionScheme,
)


class TransactionService:
    def __init__(
        self,
        identity_provider: IdProvider,
        transaction_repository: TransactionRepository,
    ):
        self.identity_provider = identity_provider
        self.transaction_repository = transaction_repository

    async def read_transactions(
        self, data: ReadTransactionsRequest
    ) -> ReadTransactionsResponse:
        transactions, total = await self.transaction_repository.get_list(data)

        return ReadTransactionsResponse(
            transactions=[
                WaterVendingTransactionScheme.model_validate(
                    transaction, from_attributes=True
                )
                for transaction in transactions
            ],
            total=total,
        )
