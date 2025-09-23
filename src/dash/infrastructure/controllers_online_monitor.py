from aiogram import Bot
from dishka import AsyncContainer
from structlog import get_logger
from dash.infrastructure.rate_limiter import RateLimiter
from dash.infrastructure.repositories.controller import ControllerRepository
from dash.infrastructure.storages.iot import IoTStorage
from dash.services.common.check_online_interactor import CheckOnlineInteractor
from dash.services.controller.dto import ReadControllerListRequest


logger = get_logger()


async def monitor_controllers_online(di_container: AsyncContainer) -> None:
    async with di_container() as dic:
        controller_repository = await dic.get(ControllerRepository)
        check_online_interactor = await dic.get(CheckOnlineInteractor)
        iot_storage = await dic.get(IoTStorage)
        bot = await dic.get(Bot)
        rate_limiter = await dic.get(RateLimiter)

        controllers, _ = await controller_repository.get_list_all(
            ReadControllerListRequest(limit=None)
        )
        for controller in controllers:
            if not controller.company:
                continue

            current_online = await check_online_interactor(controller)
            last_online = await iot_storage.get_last_online_status(controller.id)

            chat_id = controller.company.tg_chat_id

            if current_online != last_online:
                await iot_storage.set_last_online_status(controller.id, current_online)

                if not chat_id:
                    continue

                if current_online is True:
                    text = f"Пристрій {controller.name} ({controller.device_id}) в мережі ✅"
                else:
                    text = f"Пристрій {controller.name} ({controller.device_id}) не в мережі ⚠️"

                await rate_limiter.enforce_with_retry("tg_send")
                await bot.send_message(chat_id, text)
