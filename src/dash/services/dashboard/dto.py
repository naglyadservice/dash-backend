from datetime import date, datetime

from pydantic import BaseModel, model_validator

from dash.models.payment import PaymentGatewayType
from dash.services.common.dto import BaseFilters
from dash.services.common.errors.base import ValidationError


class RevenueDTO(BaseModel):
    total: int
    today: int


class GatewayAnalyticsDTO(BaseModel):
    gateway_type: PaymentGatewayType
    amount: int
    percentage: float


class PaymentAnalyticsDTO(BaseModel):
    cashless_percentage: float
    gateway_analytics: list[GatewayAnalyticsDTO]


class ActiveControllersDTO(BaseModel):
    total: int
    active: int


class TodayClientsDTO(BaseModel):
    count: int


class TransactionStatsDTO(BaseModel):
    date: date
    total: int
    bill: int
    coin: int
    qr: int
    paypass: int
    card: int


class PaymentStatsDTO(BaseModel):
    date: date
    total: int
    cash: int
    cashless: int
    paypass: int
    liqpay: int
    monopay: int


class GetRevenueRequest(BaseFilters):
    pass


class GetPaymentAnalyticsRequest(BaseFilters):
    date_from: datetime
    date_to: datetime


class GetControllersRequest(BaseFilters):
    pass


class ReadDashboardStatsRequest(BaseFilters):
    date_from: datetime
    date_to: datetime

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, datetime]) -> dict[str, datetime]:
        if values["date_from"] > values["date_to"]:
            raise ValidationError("date_from should be less than date_to")

        return values


class ReadTransactionStatsRequest(ReadDashboardStatsRequest):
    pass


class ReadPaymentStatsRequest(ReadDashboardStatsRequest):
    pass


class ReadDashboardStatsResponse(BaseModel):
    revenue: RevenueDTO
    payment_analytics: PaymentAnalyticsDTO
    active_controllers: ActiveControllersDTO
    today_clients: TodayClientsDTO
    transaction_stats: list[TransactionStatsDTO]
    payment_stats: list[PaymentStatsDTO]
