from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from dash.infrastructure.monopay import (
    CreateInvoiceRequest,
    CreateInvoiceResponse,
    MonopayService,
    ProcessWebhookRequest,
)

acquiring_router = APIRouter(
    prefix="/acquiring", tags=["ACQUIRING"], route_class=DishkaRoute
)


class MonopayInvoiceRequest(BaseModel):
    controller_id: int
    amount: int


@acquiring_router.post("/monopay/invoice")
async def request_invoice(
    request: Request,
    monopay_service: FromDishka[MonopayService],
    data: MonopayInvoiceRequest,
) -> CreateInvoiceResponse:
    return await monopay_service.create_invoice(
        CreateInvoiceRequest(
            **data.model_dump(),
            webhook_url=str(request.url_for("monopay_webhook")),
        )
    )


@acquiring_router.post("/monopay/webhook")
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
