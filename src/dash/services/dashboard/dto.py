from datetime import date

from pydantic import BaseModel

from dash.models.payment import PaymentGatewayType
from dash.services.common.dto import BaseFilters


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


class GetRevenueRequest(BaseFilters):
    pass


class GetPaymentAnalyticsRequest(BaseFilters):
    period: int


class GetControllersRequest(BaseFilters):
    pass


class ReadDashboardStatsRequest(BaseFilters):
    period: int = 30


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
