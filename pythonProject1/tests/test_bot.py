"""Интеграционные тесты для входных обработчиков бота."""
from datetime import datetime

import pytest
from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, PhotoSize
from aiogram_test_framework import AsyncBotTestMixin, TestClient

from app import setup_dispatcher


@pytest.fixture
async def client() -> TestClient:
    """Фикстура для запуска тестового клиента с имплементацией роутеров."""
    client = await TestClient.create(
        bot_token="123456:ABC",
        bot_id=123456,
        bot_username="test_bot",
        bot_first_name="Test Bot",
        setup_dispatcher_func=setup_dispatcher,
    )
    yield client
    await client.close()


class TestBotHandlers(AsyncBotTestMixin):
    """Проверка основных сценариев общения с ботом."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        self.client = await self.setup_client(
            setup_dispatcher_func=setup_dispatcher,
        )
        yield
        await self.client.close()
        self.reset_factories()

    async def test_test_command(self):
        user = self.client.create_user()
        await user.send_command("test")
        assert user.has_received_message_containing("хэш")

    async def test_start_command(self):
        user = self.client.create_user()
        await user.send_command("start")
        assert user.has_received_message_containing("Use /Test")

    async def test_regular_message(self):
        user = self.client.create_user()
        await user.send_message("Hello bot")
        assert user.has_received_message_containing("Популярность")

    async def test_photo_message_model(self):
        """Проверка структуры фотографий в Telegram-событии."""
        user = self.client.create_user(user_id=12345, first_name="TestUser")
        photo_message = Message(
            message_id=123,
            date=int(datetime.now().timestamp()),
            chat=Chat(id=user.user_id, type="private"),
            from_user=user.user,
            photo=[
                PhotoSize(
                    file_id="test_file_id",
                    file_unique_id="unique_photo",
                    width=1280,
                    height=720,
                )
            ],
            caption="Nice pic",
        )

        assert photo_message.photo
        assert photo_message.photo[-1].file_id == "test_file_id"
        assert photo_message.caption == "Nice pic"
