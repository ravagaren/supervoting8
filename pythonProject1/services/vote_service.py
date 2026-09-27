"""Логика голосования, не зависящая от маршрутизации Telegram."""
from typing import Tuple

from aiogram.types import CallbackQuery

from state_manager import state_manager
from utils.like_counter import extract_likes_from_message_text

LIKE_ACTION = "✅like"
SUPER_LIKE_ACTION = "✅super_like"
SUPER_LIKE_UNAVAILABLE = "Супер симпатия пока недоступна"
INITIAL_RATING_TEXT = "Рейтинг анкеты(0.0)"


class VoteService:
    """Обрабатывает callback-события голосования."""

    def __init__(self, message_service):
        self.message_service = message_service

    @staticmethod
    def parse_callback(data: str) -> Tuple[str, str]:
        """Разобрать ``action:chat_id:message_id``.

        Разделение выполняется только по первому двоеточию, поэтому ключ
        ``chat_id:message_id`` сохраняется целиком.
        """
        parts = (data or "").split(":", 1)
        if len(parts) != 2 or not parts[1]:
            raise ValueError("Invalid callback data format")
        return parts[0], parts[1]

    async def process(self, callback: CallbackQuery) -> None:
        """Обновить состояние голосования и перерисовать сообщение."""
        action, message_key = self.parse_callback(callback.data)
        rating = state_manager.get_message_rating(message_key)
        html = getattr(callback.message, "html_text", None) or ""
        if INITIAL_RATING_TEXT not in html and rating.like == 0 and rating.super_like == 0:
            likes, super_likes = await extract_likes_from_message_text(html)
            state_manager.set_message_rating(message_key, likes, super_likes)

        user_id = callback.from_user.id
        if action == LIKE_ACTION:
            state_manager.increment_message_like(message_key)
            state_manager.increment_user_like(user_id, message_key)
            await callback.answer()
        elif action == SUPER_LIKE_ACTION:
            if state_manager.has_user_voted_super_like(user_id, message_key):
                await callback.answer(text=SUPER_LIKE_UNAVAILABLE, show_alert=True)
                return
            state_manager.increment_message_super_like(message_key)
            state_manager.increment_user_super_like(user_id, message_key)
            await callback.answer()
        else:
            return

        await self.message_service.update_message_rating(
            callback.message, message_key, callback.from_user.first_name
        )
