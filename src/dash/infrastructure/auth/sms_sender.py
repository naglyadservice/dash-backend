from fastapi import HTTPException

from dash.infrastructure.api_client import APIClient
from dash.main.config import SMSConfig


class SMSClient:
    def __init__(self, config: SMSConfig) -> None:
        self.api_client = APIClient()
        self.config = config

    async def send_sms(self, recipients: list[str], message: str) -> None:
        _, status = await self.api_client.make_request(
            method="POST",
            url="https://api.turbosms.ua/message/send.json",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            json={
                "recipients": recipients,
                "sms": {
                    "sender": "NAGLYAD.PRO",
                    "text": message,
                },
            },
        )
        if status != 200:
            raise HTTPException(status_code=503, detail="Failed to send SMS")
