"""Форматирование и редактирование сообщений Telegram."""
import hashlib
import html
import logging
import re

from aiogram import Bot, types
from aiogram.types import LinkPreviewOptions
from aiogram.utils.formatting import Bold, Pre, Text, as_line

import config
from services.rating_service import rating_service
from state_manager import state_manager
from utils.like_counter import extract_likes_from_message_text

logger = logging.getLogger(__name__)
SEPARATOR = "_________________"
INITIAL_RATING_TEXT = "Рейтинг анкеты(0.0)"
OWNER_RATING_PREFIX = "<b>Рейтинг владельца:</b> "
AUTHOR_HASH_PREFIX = "<b>Хэш автора:</b> "
PROFILE_PREFIX = "<blockquote expandable>"
PROFILE_SUFFIX = "</blockquote>"
OPTIONS = LinkPreviewOptions(prefer_large_media=True, show_above_text=True)


class MessageFormatter:
    """Подготавливает и правит HTML-текст анкеты с рейтингом владельца и голосованием."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    def normalize_profile_text(profile_text: str) -> str:
        """Нормализует текст анкеты автора для вычисления хэша."""
        return re.sub(r"\s+", " ", html.unescape(profile_text or "")).strip()

    @staticmethod
    def format_profile_text_for_html(profile_text: str) -> str:
        """Сохраняет переносы строк при вставке профиля в HTML Telegram."""
        escaped = html.escape(profile_text or "", quote=False)
        return escaped.replace("\r\n", "\n").replace("\n", "\n")

    @classmethod
    def calculate_author_hash(cls, profile_text: str) -> str:
        """Хэш текста анкеты автора. Пока без версионности, как и было согласовано."""
        normalized = cls.normalize_profile_text(profile_text)
        if not normalized:
            return ""
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    async def add_owner_rating_line(self, message_text: str, owner_rating: int) -> str:
        """Добавляет строку рейтинга владельца после основного контента."""
        owner_line = f"{OWNER_RATING_PREFIX}{owner_rating}\n"
        return message_text + "\n" + owner_line

    async def add_author_profile_block(self, message_text: str, profile_text: str | None = None) -> str:
        """Добавляет только хэш профиля автора без самого текста профиля.

        Если profile_text не передан, использует TEST_USER_PROFILE из конфига.
        """
        # Если профиль не передан, использовать константу из конфига
        if profile_text is None:
            profile_text = config.TEST_USER_PROFILE

        normalized = self.normalize_profile_text(profile_text)
        if not normalized:
            return message_text

        author_hash = self.calculate_author_hash(normalized)
        return message_text + f"\n{AUTHOR_HASH_PREFIX}{author_hash}\n"

    async def extract_author_profile(self, message_text: str) -> tuple[str | None, str | None]:
        """Извлекает профиль автора и хэш из текста сообщения."""
        start = message_text.find(PROFILE_PREFIX)
        if start == -1:
            return None, None

        profile_start = start + len(PROFILE_PREFIX)
        profile_end = message_text.find(PROFILE_SUFFIX, profile_start)
        if profile_end == -1:
            return None, None

        profile_html = message_text[profile_start:profile_end]
        profile_text = html.unescape(profile_html)
        profile_text = re.sub(r"<br\s*/?>", "\n", profile_text, flags=re.IGNORECASE)
        profile_text = re.sub(r"\n+", "\n", profile_text).strip()

        hash_start = message_text.find(AUTHOR_HASH_PREFIX)
        if hash_start == -1:
            return profile_text, None

        hash_start += len(AUTHOR_HASH_PREFIX)
        hash_end = message_text.find("\n", hash_start)
        author_hash = (
            message_text[hash_start:] if hash_end == -1 else message_text[hash_start:hash_end]
        ).strip()

        return profile_text, author_hash

    async def extract_owner_rating(self, message_text: str) -> int | None:
        """Извлекает сохранённый рейтинг владельца из текста сообщения."""
        start = message_text.find(OWNER_RATING_PREFIX)
        if start == -1:
            return None

        start_of_rating = start + len(OWNER_RATING_PREFIX)
        end_of_line = message_text.find("\n", start_of_rating)
        rating_text = message_text[start_of_rating:] if end_of_line == -1 else message_text[start_of_rating:end_of_line]
        try:
            return int(rating_text.strip())
        except ValueError:
            return None

    async def _get_likes_with_fallback(self, message_html_text: str, cached_likes: int, cached_super_likes: int) -> tuple[int, int]:
        """Получает лайки: сначала из кэша, затем из текста сообщения если кэш пуст."""
        if cached_likes > 0 or cached_super_likes > 0:
            return cached_likes, cached_super_likes
        likes, super_likes = await extract_likes_from_message_text(message_html_text)
        return likes, super_likes

    async def add_bottom_bar(
        self,
        message_text: str,
        likes: int,
        super_likes: int,
        user_name: str = "",
        reputation: int = 50,
    ) -> str:
        """Добавляет нижнюю секцию с рейтингом и кнопками голосования."""
        grade = rating_service.calculate_integral_grade(likes, super_likes)
        notice = rating_service.congratulation(grade, user_name, reputation)
        content = Text(
            as_line(SEPARATOR),
            as_line(Pre(Bold(notice))) if notice else as_line(""),
            as_line("Популярность", f"({grade})"),
            as_line("Отдай симпатию ❣", likes),
            as_line(" ⁸¹²⁰⁹⁷⁹"),
            as_line("Отдай супер симпатию ❤", super_likes),
            as_line(" ¹²⁹⁰⁹⁸⁷"),
        )
        return message_text + content.as_html()

    async def process_questionnaire_message(
        self,
        message: types.Message,
        content: Text,
        message_id: str,
        likes: int,
        super_likes: int,
        owner_rating: int,
        user_name: str = "",
        reply_markup=None,
        author_profile_text: str | None = None,
    ) -> None:
        """Отправляет или редактирует сообщение анкеты в Telegram."""
        html_text = content.as_html()
        if SEPARATOR not in html_text:
            prepared_text = html_text
            # Всегда добавляем только хэш профиля автора (используется TEST_USER_PROFILE если не передан)
            prepared_text = await self.add_author_profile_block(prepared_text, author_profile_text)
            text_with_owner = await self.add_owner_rating_line(prepared_text, owner_rating)
            text = await self.add_bottom_bar(text_with_owner, likes, super_likes, user_name)
            await self.bot.send_message(
                message.chat.id,
                text,
                link_preview_options=OPTIONS,
                reply_markup=reply_markup,
            )
            state_manager.set_message_rating(message_id, likes, super_likes, owner_rating)
            return

        existing = getattr(message, "html_text", None) or ""
        likes, super_likes = await self._get_likes_with_fallback(existing, likes, super_likes)
        index = existing.find(SEPARATOR)
        base = existing[:index] if index >= 0 else existing
        text = await self.add_bottom_bar(base, likes, super_likes, user_name)
        await self.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=message.message_id,
            link_preview_options=OPTIONS,
            reply_markup=reply_markup,
        )
        state_manager.set_message_rating(message_id, likes, super_likes)

    async def update_message_with_rating(
        self,
        message: types.Message,
        message_id: str,
        likes: int,
        super_likes: int,
        owner_rating: int,
        user_name: str,
        reply_markup=None,
    ) -> None:
        """Обновляет лайки, сохраняя рейтинг владельца и inline-клавиатуру."""
        existing = getattr(message, "html_text", None) or ""
        likes, super_likes = await self._get_likes_with_fallback(existing, likes, super_likes)

        index = existing.find(SEPARATOR)
        base = existing[:index] if index >= 0 else existing
        extracted_rating = await self.extract_owner_rating(base)
        preserved_owner_rating = extracted_rating if extracted_rating is not None else owner_rating
        text = await self.add_bottom_bar(
            base, likes, super_likes, user_name, reputation=preserved_owner_rating
        )
        await self.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=message.message_id,
            link_preview_options=OPTIONS,
            reply_markup=reply_markup,
        )
        state_manager.set_message_rating(message_id, likes, super_likes, preserved_owner_rating)


# Backward-compatible aliases for older imports.
def build_author_hash(profile_text: str) -> str:
    """Удобная обёртка для вычисления хэша автора."""
    return MessageFormatter.calculate_author_hash(profile_text)
