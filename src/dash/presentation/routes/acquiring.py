from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Form, HTTPException, Request
from pydantic import BaseModel

from dash.infrastructure.acquiring.liqpay import (
    CreateLiqpayInvoiceRequest,
    CreateLiqpayInvoiceResponse,
    LiqpayService,
    ProcessLiqpayWebhookRequest,
)
from dash.infrastructure.acquiring.monopay import (
    CreateInvoiceRequest,
    CreateInvoiceResponse,
    MonopayService,
    ProcessWebhookRequest,
)

acquiring_router = APIRouter(
    prefix="/acquiring", tags=["ACQUIRING"], route_class=DishkaRoute
)


class MonopayInvoiceRequest(BaseModel):
    controller_id: UUID
    amount: int


@acquiring_router.post("/monopay/invoice")
async def monopay_invoice(
    monopay_service: FromDishka[MonopayService],
    data: MonopayInvoiceRequest,
) -> CreateInvoiceResponse:
    return await monopay_service.create_invoice(
        CreateInvoiceRequest(**data.model_dump())
    )


@acquiring_router.post("/monopay/webhook", include_in_schema=False)
async def monopay_webhook(
    request: Request, monopay_service: FromDishka[MonopayService]
) -> dict[str, str]:
    body = await request.body()
    x_sign = request.headers.get("X-Sign")

    if not x_sign:
        raise HTTPException(status_code=400, detail="X-Sign header is required")

    if not body:
        raise HTTPException(status_code=400, detail="Request body is required")

    await monopay_service.process_webhook(
        ProcessWebhookRequest(body=body, signature=x_sign)
    )

    return {"status": "success"}


@acquiring_router.post("/liqpay/invoice")
async def liqpay_invoice(
    liqpay_service: FromDishka[LiqpayService],
    data: CreateLiqpayInvoiceRequest,
) -> CreateLiqpayInvoiceResponse:
    return await liqpay_service.create_invoice(data)


@acquiring_router.post("/liqpay/webhook", include_in_schema=False)
async def liqpay_webhook(
    liqpay_service: FromDishka[LiqpayService],
    data: str = Form(...),
    signature: str = Form(...),
) -> dict[str, str]:
    await liqpay_service.process_webhook(
        ProcessLiqpayWebhookRequest(body=data, signature=signature)
    )
    return {"status": "success"}
