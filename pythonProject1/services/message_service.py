"""Приложение-level processing of questionnaire messages."""
import asyncio
import html
import logging
import re
from typing import TYPE_CHECKING

import aiohttp
from aiogram import Bot, types

import config
from interfaces import MessageFormatterProtocol
from keyboards.keyboard_builder import keyboard_builder
from services.author_profile_service import AuthorProfileService
from services.owner_fingerprint_service import RandomOwnerFingerprintService
from state_manager import state_manager
from utils.imgbb import get_and_upload_photo_to_imgbb
from utils.refine_form_text import refine_form_text
from utils.useful_utils import (
    analysis_message_and_rating_calculation,
    generate_test_content_message,
)
from utils.telegram_keys import message_key

if TYPE_CHECKING:
    from aiogram.utils.formatting import Text

logger = logging.getLogger(__name__)

# Задержка перед удалением исходного сообщения пользователя (в секундах)
DELETE_MESSAGE_DELAY = 10


class MessageService:
    """Сервис обработки входящих сообщений с анализом владельца контента.

    Этот сервис интегрирует весь pipeline обработки сообщений:
    1. Получает текст или фото от пользователя
    2. Проверяет владельца через OwnerFingerprintService
    3. Получает текущий рейтинг из памяти
    4. Форматирует сообщение с рейтингом владельца и профилем автора
    5. Отправляет или редактирует Telegram-сообщение
    """

    def __init__(
        self,
        bot: Bot,
        http_session: aiohttp.ClientSession | None = None,
        owner_fingerprint_service: RandomOwnerFingerprintService | None = None,
    ):
        self.bot = bot
        self.http_session = http_session
        self.summary: list[str] = ["Анкета"]
        self.formatter: MessageFormatterProtocol | None = None
        self.owner_fingerprint_service = owner_fingerprint_service or RandomOwnerFingerprintService()
        self.author_profile_service = AuthorProfileService()

    def set_formatter(self, formatter: MessageFormatterProtocol) -> None:
        """Назначить механизм форматирования и отправки текста."""
        self.formatter = formatter

    def _ensure_formatter(self) -> MessageFormatterProtocol:
        """Вернуть настроенный форматтер или выкинуть понятную ошибку."""
        if self.formatter is None:
            raise RuntimeError("MessageFormatter must be configured before processing messages")
        return self.formatter

    @staticmethod
    def _extract_author_profile_from_text(payload: str | None) -> str | None:
        """Извлечь текст анкеты автора из payload, если присутствует в новом формате.

        Ищет видимый профиль в формате:
        - HTML-строка вида <i>...</i> после заголовка "Профиль автора:"

        Если профиль не найден, возвращает None (будет использован TEST_USER_PROFILE).
        """
        if not payload:
            return None

        # Ищем видимый профиль в курсиве (новый формат)
        match = re.search(r"<b>Профиль автора:</b>\s*\n<i>(.*?)</i>", payload, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return html.unescape(match.group(1)).strip()

        # Fallback: старый формат в blockquote (если существует)
        match = re.search(r"<blockquote>(.*?)</blockquote>", payload, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return html.unescape(match.group(1)).strip()

        return None

    async def _analysis(self, message: types.Message):
        """Собрать результат анализа и текущий рейтинг для сообщения."""
        result = await analysis_message_and_rating_calculation(
            message=message,
            local_user_ratings=state_manager.get_all_user_ratings(),
            local_message_ratings=state_manager.get_all_message_ratings(),
        )
        return result, state_manager.get_message_rating(result.origin_message_id)

    async def _check_owner(self, message: types.Message) -> int:
        """Проверить владельца контента и вернуть его рейтинг."""
        author_profile_text = self._extract_author_profile_from_text(message.text or "")

        if author_profile_text:
            owner_rating = await self.author_profile_service.resolve_owner(author_profile_text)
            logger.debug(
                "Owner determined from author profile for message %d: rating=%d",
                message.message_id,
                owner_rating,
            )
            return owner_rating

        owner_result = await self.owner_fingerprint_service.check(message)
        logger.debug(
            "Owner fingerprint check for message %d: status=%s, rating=%d",
            message.message_id,
            owner_result.status,
            owner_result.owner_rating,
        )
        return owner_result.owner_rating

    async def process_text(self, message: types.Message) -> None:
        """Обработать текстовую анкету и передать её в форматтер."""
        result, rating = await self._analysis(message)
        owner_rating = await self._check_owner(message)
        text = message.text or ""
        # Пытаемся извлечь профиль из текста входящего сообщения
        # Если не найден, будет использован TEST_USER_PROFILE из конфига
        author_profile_text = self._extract_author_profile_from_text(text)

        self.summary.append(text)
        self.summary = refine_form_text(self.summary)
        if not self.summary:
            return
        content = await generate_test_content_message(self.summary[0], text)
        # Передаём None если профиль не найден — formatter сам использует TEST_USER_PROFILE
        await self._ensure_formatter().process_questionnaire_message(
            message,
            content,
            result.origin_message_id,
            rating.like,
            rating.super_like,
            owner_rating,
            message.from_user.first_name or "",
            result.builder.as_markup(),
            author_profile_text=author_profile_text,
        )

    async def _delete_user_message_delayed(self, chat_id: int, message_id: int) -> None:
        """Удалить сообщение пользователя с задержкой, чтобы бот успел отправить новое.
        
        Args:
            chat_id: ID чата, в котором находится сообщение.
            message_id: ID сообщения для удаления.
        """
        await asyncio.sleep(DELETE_MESSAGE_DELAY)
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info("Deleted user's photo message %d from chat %d after %d second delay", 
                       message_id, chat_id, DELETE_MESSAGE_DELAY)
        except Exception:
            logger.exception("Failed to delete user's photo message %d from chat %d", message_id, chat_id)

    async def process_photo(self, message: types.Message) -> None:
        """Обработать фото: скачать, загрузить и собрать анкету с рейтингом владельца.
        
        После создания нового сообщения удаляет исходное сообщение пользователя
        с задержкой в 10 секунд, чтобы бот успел отправить новое сообщение.
        """
        result, rating = await self._analysis(message)
        owner_rating = await self._check_owner(message)
        # Пытаемся извлечь профиль из подписи к фото
        # Если не найден, будет использован TEST_USER_PROFILE из конфига
        author_profile_text = self._extract_author_profile_from_text(message.caption or "")
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
        # Передаём None если профиль не найден — formatter сам использует TEST_USER_PROFILE
        await self._ensure_formatter().process_questionnaire_message(
            message,
            content,
            result.origin_message_id,
            rating.like,
            rating.super_like,
            owner_rating,
            message.from_user.first_name or "",
            result.builder.as_markup(),
            author_profile_text=author_profile_text,
        )
        
        # Удаляем исходное сообщение пользователя с задержкой
        asyncio.create_task(self._delete_user_message_delayed(message.chat.id, message.message_id))

    async def update_message_rating(self, message: types.Message, message_key_str: str, user_name: str) -> None:
        """Перерисовать нижнюю часть анкеты, сохранив inline-клавиатуру и рейтинг владельца."""
        rating = state_manager.get_message_rating(message_key_str)
        builder = keyboard_builder(
            {"like": rating.like, "super_like": rating.super_like}, message_key_str,
        )
        owner_rating = 50
        await self._ensure_formatter().update_message_with_rating(
            message,
            message_key_str,
            rating.like,
            rating.super_like,
            owner_rating,
            user_name,
            reply_markup=builder.as_markup(),
        )
