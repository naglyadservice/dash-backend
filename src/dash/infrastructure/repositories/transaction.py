from dash.infrastructure.repositories.base import BaseRepository
from dash.models.transactions.transaction import Transaction


class TransactionRepository(BaseRepository):
    async def create_transaction(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction
