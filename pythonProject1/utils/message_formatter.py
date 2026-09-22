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
OPTIONS = LinkPreviewOptions(prefer_large_media=True, show_above_text=True)


class MessageFormatter:
    """Подготавливает и правит HTML-текст анкеты с нижней панелью рейтинга."""

    def __init__(self, bot: Bot):
        self.bot = bot

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
            as_line(" ���¹²⁰⁹⁷⁹"),
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
        user_name: str = "",
        reply_markup=None,
    ) -> None:
        """Отправляет или редактирует сообщение анкеты в Telegram."""
        html = content.as_html()
        if SEPARATOR not in html:
            text = await self.add_bottom_bar(html, likes, super_likes, user_name)
            await self.bot.send_message(
                message.chat.id,
                text,
                link_preview_options=OPTIONS,
                reply_markup=reply_markup,
            )
            state_manager.set_message_rating(message_id, likes, super_likes)
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
        user_name: str,
        reply_markup=None,
    ) -> None:
        """Обновляет рейтинг без удаления inline-клавиатуры."""
        existing = getattr(message, "html_text", None) or ""
        if INITIAL_RATING_TEXT not in existing and likes == 0 and super_likes == 0:
            likes, super_likes = await like_counter(message_id, existing)
        index = existing.find(SEPARATOR)
        base = existing[:index] if index >= 0 else existing
        text = await self.add_bottom_bar(base, likes, super_likes, user_name, reputation=43)
        await self.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=message.message_id,
            link_preview_options=OPTIONS,
            reply_markup=reply_markup,
        )
        state_manager.set_message_rating(message_id, likes, super_likes)
