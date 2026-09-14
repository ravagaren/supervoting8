import asyncio
import logging
from typing import Optional

import config

from handlers.control_commands import router
# register other handlers (they register routes on import)
from handlers import photo, text, callbacks  # noqa: F401

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import aiohttp

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Объект бота
bot: Bot = Bot(
    token=config.token,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
    )
)

# HTTP session для повторного использования
http_session: Optional[aiohttp.ClientSession] = None


def setup_dispatcher(bot: Bot, dispatcher: Dispatcher) -> None:
    """
    Конфигурирует dispatcher с обработчиками и middleware.
    """
    dispatcher.include_router(router)


async def main() -> None:
    """
    Главная функция запуска бота.
    """
    global http_session
    dispatcher: Dispatcher = Dispatcher()
    setup_dispatcher(bot, dispatcher)

    try:
        http_session = aiohttp.ClientSession()
        await dispatcher.start_polling(bot)
    finally:
        if http_session is not None:
            await http_session.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
