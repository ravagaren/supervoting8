"""Приложение-level processing of questionnaire messages."""
import asyncio
import html
import logging
import random
import re
from typing import TYPE_CHECKING

import aiohttp
from aiogram import Bot, types

import config
from interfaces import MessageFormatterProtocol
from keyboards.keyboard_builder import keyboard_builder
from services.author_profile_service import AuthorProfileService
from services.owner_fingerprint_service import RandomOwnerFingerprintService
from services.questionnaire_service import QuestionnaireType, questionnaire_service
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

DELETE_MESSAGE_DELAY = 10


class MessageService:
    """Сервис обработки входящих сообщений с анализом владельца контента."""

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
        """Извлечь текст анкеты автора из payload."""
        if not payload:
            return None

        match = re.search(r"<b>Профиль автора:</b>\s*\n<i>(.*?)</i>", payload, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return html.unescape(match.group(1)).strip()

        match = re.search(r"<blockquote>(.*?)</blockquote>", payload, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return html.unescape(match.group(1)).strip()

        return None

    def _build_questionnaire_user_id(self, message: types.Message | None) -> int:
        """Вернуть user_id для сохранения анкеты. Для тестового режима возможна генерация."""
        if message is not None and getattr(message, "from_user", None) is not None:
            user_id = message.from_user.id
            if user_id:
                return int(user_id)
        return random.randint(100_000_000, 999_999_999)

    async def _save_questionnaire_to_storage(
        self,
        message: types.Message,
        questionnaire_type: QuestionnaireType,
        gender: str | None = None,
        age: str | None = None,
        address: str | None = None,
        positioning: str | None = None,
    ) -> None:
        """Сохранить анкету в целевой чат/тред конфигурации."""
        user_id = self._build_questionnaire_user_id(message)
        chat_id = int(config.QUESTIONNAIRE_STORAGE_CHAT_ID)
        thread_id = int(getattr(config, "QUESTIONNAIRE_STORAGE_THREAD_ID", 0) or 0)

        if questionnaire_type == QuestionnaireType.FULL:
            questionnaire = questionnaire_service.create_full_questionnaire(
                user_id=user_id,
                chat_id=chat_id,
                gender=gender,
                age=age,
                address=address,
                positioning=positioning,
            )
        else:
            questionnaire = questionnaire_service.create_short_questionnaire(
                user_id=user_id,
                chat_id=chat_id,
                gender=gender,
                age=age,
                address=address,
                positioning=positioning,
            )

        text = questionnaire_service.format_questionnaire_text(questionnaire)
        try:
            payload = {"chat_id": chat_id, "text": text}
            if thread_id:
                payload["message_thread_id"] = thread_id
            await self.bot.send_message(**payload)
            logger.info(
                "Stored %s questionnaire for user %d in chat %d (thread %s)",
                questionnaire_type.value,
                user_id,
                chat_id,
                thread_id or "default",
            )
        except Exception:
            logger.exception(
                "Failed to store %s questionnaire for user %d to chat %d thread %s",
                questionnaire_type.value,
                user_id,
                chat_id,
                thread_id or "default",
            )

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

    async def _delete_user_message_delayed(self, chat_id: int, message_id: int, message_type: str = "message") -> None:
        """Удалить сообщение пользователя с задержкой."""
        await asyncio.sleep(DELETE_MESSAGE_DELAY)
        try:
            await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            logger.info("Deleted user's %s message %d from chat %d after %d second delay",
                        message_type, message_id, chat_id, DELETE_MESSAGE_DELAY)
        except Exception:
            logger.exception("Failed to delete user's %s message %d from chat %d", message_type, message_id, chat_id)

    async def process_text(self, message: types.Message) -> None:
        """Обработать текстовую анкету и передать её в форматтер."""
        result, rating = await self._analysis(message)
        owner_rating = await self._check_owner(message)
        text = message.text or ""
        author_profile_text = self._extract_author_profile_from_text(text)

        self.summary.append(text)
        self.summary = refine_form_text(self.summary)
        if not self.summary:
            return

        await self._save_questionnaire_to_storage(
            message=message,
            questionnaire_type=QuestionnaireType.SHORT,
            gender=None,
            age=None,
            address=None,
            positioning=None,
        )

        content = await generate_test_content_message(self.summary[0], text)
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

        asyncio.create_task(self._delete_user_message_delayed(message.chat.id, message.message_id, "text"))

    async def process_photo(self, message: types.Message) -> None:
        """Обработать фото: скачать, загрузить и собрать анкету с рейтингом владельца."""
        result, rating = await self._analysis(message)
        owner_rating = await self._check_owner(message)
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

        await self._save_questionnaire_to_storage(
            message=message,
            questionnaire_type=QuestionnaireType.SHORT,
            gender=None,
            age=None,
            address=None,
            positioning=None,
        )

        content = await generate_test_content_message(image_url, message.caption or "")
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

        asyncio.create_task(self._delete_user_message_delayed(message.chat.id, message.message_id, "photo"))

    async def create_manual_questionnaire(
        self,
        message: types.Message,
        questionnaire_type: QuestionnaireType,
        gender: str | None = None,
        age: str | None = None,
        address: str | None = None,
        positioning: str | None = None,
    ) -> None:
        """Командный метод для создания полной/сокращённой анкеты вручную."""
        await self._save_questionnaire_to_storage(
            message=message,
            questionnaire_type=questionnaire_type,
            gender=gender,
            age=age,
            address=address,
            positioning=positioning,
        )

    async def update_message_rating(self, message: types.Message, message_key_str: str, user_name: str) -> None:
        """Перерисовать нижнюю часть анкеты, сохранив inline-клавиатуру и актуальный рейтинг владельца."""
        rating = state_manager.get_message_rating(message_key_str)
        builder = keyboard_builder(
            {"like": rating.like, "super_like": rating.super_like}, message_key_str,
        )
        owner_rating = rating.owner_rating if rating.owner_rating is not None else 1
        await self._ensure_formatter().update_message_with_rating(
            message,
            message_key_str,
            rating.like,
            rating.super_like,
            owner_rating,
            user_name,
            reply_markup=builder.as_markup(),
        )

