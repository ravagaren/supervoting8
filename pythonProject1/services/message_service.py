"""Приложение-level processing of questionnaire messages."""
import logging
from typing import TYPE_CHECKING

import aiohttp
from aiogram import Bot, types

import config
from interfaces import MessageFormatterProtocol
from keyboards.keyboard_builder import keyboard_builder
from state_manager import state_manager
from utils.imgbb import get_and_upload_photo_to_imgbb
from utils.refine_form_text import refine_form_text
from utils.useful_utils import (
    analysis_message_and_rating_calculation,
    generate_test_content_message,
)

if TYPE_CHECKING:
    from aiogram.utils.formatting import Text

logger = logging.getLogger(__name__)


class MessageService:
    """Сервис обработки входящих сообщений анкеты."""

    def __init__(self, bot: Bot, http_session: aiohttp.ClientSession | None = None):
        # Экземпляр бота Telegram для запроса metadata и отправки сообщений.
        self.bot = bot
        # Общая HTTP-сессия для загрузки файлов и внешних запросов.
        self.http_session = http_session
        # История текста анкеты для формирования итогового содержания.
        self.summary: list[str] = ["Анкета"]
        # Форматтер подключается извне в точке сборки приложения.
        self.formatter: MessageFormatterProtocol | None = None

    def set_formatter(self, formatter: MessageFormatterProtocol) -> None:
        """Назначить механизм форматирования и отправки текста."""
        self.formatter = formatter

    def _ensure_formatter(self) -> MessageFormatterProtocol:
        """Вернуть настроенный форматтер или выкинуть понятную ошибку."""
        if self.formatter is None:
            raise RuntimeError("MessageFormatter must be configured before processing messages")
        return self.formatter

    async def _analysis(self, message: types.Message):
        """Собрать результат анализа и текущий рейтинг для сообщения."""
        result = await analysis_message_and_rating_calculation(
            message=message,
            local_user_ratings=state_manager.get_all_user_ratings(),
            local_message_ratings=state_manager.get_all_message_ratings(),
        )
        return result, state_manager.get_message_rating(result.origin_message_id)

    async def process_text(self, message: types.Message) -> None:
        """Обработать текстовую анкету и передать её в форматтер."""
        result, rating = await self._analysis(message)
        text = message.text or ""
        self.summary.append(text)
        self.summary = refine_form_text(self.summary)
        if not self.summary:
            return
        content = await generate_test_content_message(self.summary[0], text)
        await self._ensure_formatter().process_questionnaire_message(
            message, content, result.origin_message_id, rating.like, rating.super_like,
            message.from_user.first_name or "", result.builder.as_markup(),
        )

    async def process_photo(self, message: types.Message) -> None:
        """Обработать фото: скачать, загрузить и собрать анкету."""
        result, rating = await self._analysis(message)
        photo = message.photo[-1]
        image_url = photo.file_id
        try:
            file_info = await self.bot.get_file(photo.file_id)
            file_path = getattr(file_info, "file_path", None)
            if file_path:
                image_url = await get_and_upload_photo_to_imgbb(
                    file_path, config.token, config.imgbb_api_key, session=self.http_session,
                ) or photo.file_id
            else:
                logger.warning("Telegram returned no file path for photo %s", photo.file_id)
        except Exception:
            logger.exception("Could not upload photo %s; using file_id fallback", photo.file_id)
        content = await generate_test_content_message(image_url, message.caption or "")
        await self._ensure_formatter().process_questionnaire_message(
            message, content, result.origin_message_id, rating.like, rating.super_like,
            message.from_user.first_name or "", result.builder.as_markup(),
        )

    async def update_message_rating(self, message: types.Message, message_id: str, user_name: str) -> None:
        """Перерисовать нижнюю часть анкеты, сохранив inline-клавиатуру."""
        rating = state_manager.get_message_rating(message_id)
        builder = keyboard_builder(
            {"like": rating.like, "super_like": rating.super_like}, message_id,
        )
        await self._ensure_formatter().update_message_with_rating(
            message, message_id, rating.like, rating.super_like, user_name,
            reply_markup=builder.as_markup(),
        )
