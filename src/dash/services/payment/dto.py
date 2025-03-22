from datetime import datetime

from pydantic import BaseModel, ConfigDict

from dash.models.payment import PaymentStatus, PaymentType
from dash.services.common.pagination import Pagination


class PaymentScheme(BaseModel):
    id: int
    controller_id: int
    amount: int
    status: PaymentStatus
    type: PaymentType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReadPaymentsRequest(Pagination):
    controller_id: int | None = None


class ReadPaymentsResponse(BaseModel):
    payments: list[PaymentScheme]
    total: int
