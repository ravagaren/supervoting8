"""Дефолтный bootstrap приложения и подключение зависимостей."""
import asyncio
import logging
from typing import Optional

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from handlers import configure_services, register_all_handlers
from services.db_bootstrap import bootstrap_application_data
from services.message_service import MessageService
from utils.message_formatter import MessageFormatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    """Создать экземпляр бота с HTML-форматированием текста."""
    return Bot(token=config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def setup_dispatcher(
    bot: Bot,
    dispatcher: Dispatcher,
    http_session: Optional[aiohttp.ClientSession] = None,
) -> MessageService:
    """Подключить обработчики и сервисы к диспетчеру."""
    message_service = MessageService(bot, http_session=http_session)
    message_service.set_formatter(MessageFormatter(bot))
    configure_services(message_service)
    register_all_handlers(dispatcher)
    return message_service


async def main() -> None:
    """Запуск polling-цикла бота и подготовка HTTP-сессии."""
    bootstrap_application_data()
    logger.info("Application bootstrap completed")

    bot = create_bot()
    dispatcher = Dispatcher()
    http_session = aiohttp.ClientSession()
    try:
        try:
            webhook = await bot.get_webhook_info()
            if webhook and webhook.url:
                logger.warning(
                    "Active Telegram webhook detected (%s). Removing it before polling.",
                    webhook.url,
                )
                await bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            logger.exception("Could not inspect or remove Telegram webhook; continuing with polling")

        setup_dispatcher(bot, dispatcher, http_session)
        logger.info("Starting bot polling")
        await dispatcher.start_polling(
            bot,
            handle_signals=True,
            drop_pending_updates=True,
        )
    finally:
        await http_session.close()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
