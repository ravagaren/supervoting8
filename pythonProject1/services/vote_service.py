"""Сервис обработки голосования (лайки и суперлайки)."""
import logging

from aiogram.types import CallbackQuery

from services.message_service import MessageService
from services.user_profile_service import user_profile_service
from state_manager import state_manager

logger = logging.getLogger(__name__)

PROFILE_REQUIRED_MSG = (
    "Сначала заполните анкету! 📝\n\n"
    "Отправьте в личное сообщение через пробел:\n"
    "<b>ник возраст город позиция</b>"
)


class VoteService:
    """Обработка голосования за анкеты."""

    def __init__(self, message_service: MessageService):
        self.message_service = message_service

    async def process(self, callback: CallbackQuery) -> None:
        """Обработать callback нажатия кнопки лайка/суперлайка."""
        user_id = callback.from_user.id

        if not user_profile_service.has_profile(user_id):
            logger.info("Vote attempt by user %d without profile", user_id)
            try:
                await callback.answer(text="Заполните анкету в личном чате", show_alert=True)
                await self.message_service.bot.send_message(
                    chat_id=user_id,
                    text=PROFILE_REQUIRED_MSG,
                    parse_mode="HTML",
                )
            except Exception:
                logger.exception("Failed to send profile required message")
            return

        if not callback.data or not callback.data.startswith("✅"):
            logger.warning("Invalid callback data: %s", callback.data)
            return

        try:
            parts = callback.data.split(":")
            if len(parts) < 2:
                logger.warning("Invalid callback format: %s", callback.data)
                return

            action = parts[0]
            message_key = ":".join(parts[1:])

            if action == "✅like":
                state_manager.increment_message_like(message_key)
                state_manager.increment_user_like(user_id, message_key)
                logger.info("User %d liked message %s", user_id, message_key)
            elif action == "✅super_like":
                state_manager.increment_message_super_like(message_key)
                state_manager.increment_user_super_like(user_id, message_key)
                logger.info("User %d super_liked message %s", user_id, message_key)
            else:
                logger.warning("Unknown vote action: %s", action)
                return

            await callback.answer()

            if callback.message:
                rating = state_manager.get_message_rating(message_key)
                await self.message_service.update_message_rating(
                    callback.message,
                    message_key,
                    rating.like,
                    rating.super_like,
                    callback.from_user.first_name or "Пользователь",
                )
        except (ValueError, IndexError) as exc:
            logger.warning("Invalid vote callback: %s", exc)
        except Exception:
            logger.exception("Error processing vote")
