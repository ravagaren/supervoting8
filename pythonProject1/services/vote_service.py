"""Vote business logic, independent from Telegram routing."""
from typing import Tuple

from aiogram.types import CallbackQuery

from state_manager import state_manager
from utils.like_counter import like_counter

LIKE_ACTION = "✅like"
SUPER_LIKE_ACTION = "✅super_like"
SUPER_LIKE_UNAVAILABLE = "Супер симпатия пока недоступна"
INITIAL_RATING_TEXT = "Рейтинг анкеты(0.0)"


class VoteService:
    def __init__(self, message_service):
        self.message_service = message_service

    @staticmethod
    def parse_callback(data: str) -> Tuple[str, str]:
        parts = (data or "").split(":", 1)
        if len(parts) != 2 or not parts[1]:
            raise ValueError("Invalid callback data format")
        return parts[0], parts[1]

    async def process(self, callback: CallbackQuery) -> None:
        action, message_id = self.parse_callback(callback.data)
        rating = state_manager.get_message_rating(message_id)
        html = getattr(callback.message, "html_text", None) or ""
        if INITIAL_RATING_TEXT not in html and rating.like == 0 and rating.super_like == 0:
            likes, super_likes = await like_counter(message_id, html)
            state_manager.set_message_rating(message_id, likes, super_likes)

        user_id = callback.from_user.id
        if action == LIKE_ACTION:
            state_manager.increment_message_like(message_id)
            state_manager.increment_user_like(user_id, message_id)
            await callback.answer()
        elif action == SUPER_LIKE_ACTION:
            if state_manager.has_user_voted_super_like(user_id, message_id):
                await callback.answer(text=SUPER_LIKE_UNAVAILABLE, show_alert=True)
                return
            state_manager.increment_message_super_like(message_id)
            state_manager.increment_user_super_like(user_id, message_id)
            await callback.answer()
        else:
            return

        await self.message_service.update_message_rating(
            callback.message, message_id, callback.from_user.first_name
        )
