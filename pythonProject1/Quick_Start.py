"""Пример тестового сценария и быстрый запуск бота."""
import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_test_framework import AsyncBotTestMixin

import config


def setup_dispatcher(bot: Bot, dispatcher: Dispatcher) -> None:
    """Подготовить диспетчер для тестового сценария."""
    # Сценарий заглушки; здесь можно подключить реальные обработчики.
    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
        ),
    )
    dispatcher = Dispatcher()


class TestMyHandler(AsyncBotTestMixin):
    """Проверка старого примера работы с командой /start."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.client = await self.setup_client(
            setup_dispatcher_func=setup_dispatcher,
        )
        yield
        await self.client.close()
        self.reset_factories()

    async def test_start_command(self):
        user = self.client.create_user()
        await user.send_command("start")
        assert user.has_received_message_containing("Welcome")
