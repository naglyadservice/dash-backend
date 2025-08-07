from typing import Any, Literal

import aiohttp


class APIClient:
    @staticmethod
    async def make_request(
        method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
        url: str,
        headers: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
                data=data,
            ) as response:
                return await response.json(), response.status
