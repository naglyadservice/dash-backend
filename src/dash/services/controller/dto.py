from datetime import datetime
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from dash.models.controllers.controller import (
    Controller,
    ControllerStatus,
    ControllerType,
)
from dash.services.common.dto import ControllerID, PublicCompanyDTO, PublicLocationDTO
from dash.services.common.errors.base import ValidationError
from dash.services.common.pagination import Pagination
from dash.services.iot.car_cleaner.dto import CarCleanerTariffDTO
from dash.services.iot.carwash.dto import CarwashTariffDTO
from dash.services.iot.vacuum.dto import VacuumTariffDTO


class BaseControllerFilters(BaseModel):
    location_id: UUID | None = None
    company_id: UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def validate(cls, values: dict[str, Any]) -> dict[str, Any]:
        filters = [
            values.get("location_id"),
            values.get("company_id"),
        ]
        active_filters = [f for f in filters if f is not None]

        if len(active_filters) > 1:
            raise ValidationError(
                "Only one filter can be used at a time. Please use either 'location_id', or 'company_id'"
            )
        return values


class ReadControllerListRequest(Pagination, BaseControllerFilters):
    type: ControllerType | None = None


class ControllerScheme(BaseModel):
    id: UUID
    device_id: str
    location_id: UUID | None
    name: str
    version: str
    type: ControllerType
    qr: str
    status: ControllerStatus
    is_online: bool = False

    @classmethod
    def make(cls, controller: Controller, is_online: bool) -> Self:
        dto = cls.model_validate(controller, from_attributes=True)
        dto.is_online = is_online
        return dto


class ReadControllerResponse(BaseModel):
    controllers: list[ControllerScheme]
    total: int


class AddControllerRequest(BaseModel):
    device_id: str
    type: ControllerType = ControllerType.WATER_VENDING
    name: str
    version: str
    status: ControllerStatus = ControllerStatus.ACTIVE


class AddControllerResponse(BaseModel):
    id: UUID


class MonopayCredentialsDTO(BaseModel):
    token: str
    is_active: bool


class AddMonopayCredentialsRequest(ControllerID):
    monopay: MonopayCredentialsDTO


class LiqpayCredentialsDTO(BaseModel):
    public_key: str
    private_key: str
    is_active: bool


class AddLiqpayCredentialsRequest(ControllerID):
    liqpay: LiqpayCredentialsDTO


class CheckboxCredentialsDTO(BaseModel):
    cashier_login: str
    cashier_password: str
    license_key: str
    good_code: str
    good_name: str
    tax_code: str | None
    is_active: bool
    fiscalize_cash: bool


class AddCheckboxCredentialsRequest(ControllerID):
    checkbox: CheckboxCredentialsDTO


class LocationID(BaseModel):
    location_id: UUID


class AddControllerLocationRequest(ControllerID, LocationID):
    pass


class EncashmentScheme(BaseModel):
    id: UUID
    created_at: datetime
    created_at_controller: datetime
    updated_at: datetime | None
    encashed_amount: int
    received_amount: int | None
    is_closed: bool
    coin_1: int
    coin_2: int
    coin_3: int
    coin_4: int
    coin_5: int
    coin_6: int
    bill_1: int
    bill_2: int
    bill_3: int
    bill_4: int
    bill_5: int
    bill_6: int
    bill_7: int
    bill_8: int

    model_config = ConfigDict(from_attributes=True)


class ReadEncashmentListRequest(Pagination):
    controller_id: UUID


class ReadEncashmentListResponse(BaseModel):
    encashments: list[EncashmentScheme]
    total: int


class CloseEncashmentRequest(BaseModel):
    encashment_id: UUID
    controller_id: UUID
    received_amount: int


class BasePublicControllerScheme(BaseModel):
    id: UUID
    name: str
    type: ControllerType
    device_id: str
    qr: str
    liqpay_active: bool
    monopay_active: bool
    min_deposit_amount: int

    model_config = ConfigDict(from_attributes=True)


class PublicCarwashScheme(BasePublicControllerScheme):
    type: Literal[ControllerType.CARWASH]
    tariff: CarwashTariffDTO


class WsmTariffDTO(BaseModel):
    tariffPerLiter_1: int
    tariffPerLiter_2: int


class PublicWsmScheme(BasePublicControllerScheme):
    type: Literal[ControllerType.WATER_VENDING]
    tariff: WsmTariffDTO


class PublicFiscalizerScheme(BasePublicControllerScheme):
    type: Literal[ControllerType.FISCALIZER]
    quick_deposit_button_1: int | None
    quick_deposit_button_2: int | None
    quick_deposit_button_3: int | None
    description: str | None


class PublicVacuumScheme(BasePublicControllerScheme):
    type: Literal[ControllerType.VACUUM]
    tariff: VacuumTariffDTO


class PublicCarCleanerScheme(BasePublicControllerScheme):
    type: Literal[ControllerType.CAR_CLEANER]
    tariff: CarCleanerTariffDTO


CONTROLLER_PUBLIC_SCHEME_TYPE = (
    PublicWsmScheme
    | PublicCarwashScheme
    | PublicFiscalizerScheme
    | PublicVacuumScheme
    | PublicCarCleanerScheme
)


class ReadPublicControllerRequest(BaseModel):
    qr: str


class ReadPublicControllerResponse(BaseModel):
    company: PublicCompanyDTO | None
    location: PublicLocationDTO | None
    controller: CONTROLLER_PUBLIC_SCHEME_TYPE


class ReadPublicControllerListRequest(BaseModel):
    location_id: UUID


class ReadPublicControllerListResponse(BaseModel):
    company: PublicCompanyDTO | None
    location: PublicLocationDTO
    controllers: list[CONTROLLER_PUBLIC_SCHEME_TYPE]


class SetupTasmotaRequest(ControllerID):
    tasmota_id: str | None


class EditControllerDTO(BaseModel):
    name: str | None = None
    version: str | None = None


class EditControllerRequest(ControllerID):
    data: EditControllerDTO


class GetEnergyStatsRequest(ControllerID):
    period: int


class GetEnergyStatsResponse(BaseModel):
    total_energy: float


class SetMinDepositAmountRequest(ControllerID):
    min_deposit_amount: int
