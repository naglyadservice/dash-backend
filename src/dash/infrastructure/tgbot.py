from typing import AsyncIterator

from aiogram import Bot
from dash.main.config import TgBotConfig


async def get_tg_bot(config: TgBotConfig) -> AsyncIterator[Bot]:
    yield Bot(token=config.token)
