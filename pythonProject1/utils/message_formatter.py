"""Форматирование и редактирование сообщений Telegram."""
import logging

from aiogram import Bot, types
from aiogram.types import LinkPreviewOptions
from aiogram.utils.formatting import Bold, Pre, Text, as_line

from services.rating_service import rating_service
from state_manager import state_manager
from utils.like_counter import like_counter

logger = logging.getLogger(__name__)
SEPARATOR = "_________________"
INITIAL_RATING_TEXT = "Рейтинг анкеты(0.0)"
OWNER_RATING_PREFIX = "<b>Рейтинг владельца:</b> "
OPTIONS = LinkPreviewOptions(prefer_large_media=True, show_above_text=True)


class MessageFormatter:
    """Подготавливает и правит HTML-текст анкеты с рейтингом владельца и голосованием."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def add_owner_rating_line(self, message_text: str, owner_rating: int) -> str:
        """Добавляет строку рейтинга владельца после основного контента."""
        owner_line = f"<b>Рейтинг владельца:</b> {owner_rating}\n"
        return message_text + "\n" + owner_line

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
            as_line(" Отдай симпатию ❣", likes),
            as_line(" ⁸¹²⁰⁹⁷⁹"),
            as_line(" Отдай супер симпатию ❤", super_likes),
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
    ) -> None:
        """Отправляет или редактирует сообщение анкеты в Telegram."""
        html = content.as_html()
        if SEPARATOR not in html:
            text_with_owner = await self.add_owner_rating_line(html, owner_rating)
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
        if INITIAL_RATING_TEXT not in existing and likes == 0 and super_likes == 0:
            likes, super_likes = await like_counter(message_id, existing)
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
        if INITIAL_RATING_TEXT not in existing and likes == 0 and super_likes == 0:
            likes, super_likes = await like_counter(message_id, existing)

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
