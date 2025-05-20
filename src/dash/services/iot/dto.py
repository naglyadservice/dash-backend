from uuid import UUID

from pydantic import BaseModel


class ControllerID(BaseModel):
    controller_id: UUID


class SetConfigRequest(ControllerID):
    config: BaseModel


class SetSettingsRequest(ControllerID):
    settings: BaseModel


class GetDisplayInfoRequest(ControllerID):
    pass


class RebootControllerRequest(ControllerID):
    delay: int


class QRPaymentDTO(BaseModel):
    order_id: str
    amount: int


class SendQRPaymentRequest(ControllerID):
    payment: QRPaymentDTO


class FreePaymentDTO(BaseModel):
    amount: int


class SendFreePaymentRequest(ControllerID):
    payment: FreePaymentDTO


class PaymentClearOptionsDTO(BaseModel):
    CoinClear: bool | None = None
    BillClear: bool | None = None
    PrevClear: bool | None = None
    FreeClear: bool | None = None
    QRcodeClear: bool | None = None
    PayPassClear: bool | None = None


class ClearPaymentsRequest(ControllerID):
    options: PaymentClearOptionsDTO


class SendActionRequest(ControllerID):
    action: BaseModel
