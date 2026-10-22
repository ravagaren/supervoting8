from __future__ import annotations

import logging

from aiogram.types import CallbackQuery

from services.message_service import MessageService
from services.user_profile_service import user_profile_service
from state_manager import state_manager
from utils.like_counter import extract_likes_from_message_text

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

    async def _hydrate_message_rating_from_text(self, message_key: str, message) -> tuple[int, int]:
        """Если в памяти ничего нет, берём текущий рейтинг из текста сообщения."""
        current = state_manager.get_message_rating(message_key)
        if current.like > 0 or current.super_like > 0:
            return current.like, current.super_like

        if message is None:
            return current.like, current.super_like

        html_text = getattr(message, "html_text", None) or getattr(message, "text", None) or ""
        if not html_text:
            return current.like, current.super_like

        likes, super_likes = await extract_likes_from_message_text(html_text)
        if likes > 0 or super_likes > 0:
            state_manager.set_message_rating(message_key, likes, super_likes)
            return likes, super_likes

        return current.like, current.super_like

    async def process(self, callback: CallbackQuery) -> None:
        user_id = callback.from_user.id

        # EVERY vote requires a filled profile, regardless of chat type.
        has_profile = await user_profile_service.has_profile_async(user_id)
        if not has_profile:
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

            # Re-check at apply-time to prevent a race where the profile is removed
            # between the initial validation and the moment the vote is written.
            if not await user_profile_service.has_profile_async(user_id):
                logger.info("Blocking vote at apply-time: user %d has no profile", user_id)
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

            try:
                chat_str, msg_str = message_key.split(":")
                chat_id = int(chat_str)
                msg_id = int(msg_str)
            except Exception:
                logger.warning("Invalid message_key format: %s", message_key)
                return

            like_count, super_like_count = await self._hydrate_message_rating_from_text(
                message_key, callback.message
            )

            if action == "✅like":
                # in-memory state only; SQLite will supply durable persistence later
                state_manager.set_message_rating(message_key, like_count + 1, super_like_count)
                state_manager.increment_user_like(user_id, message_key)
                logger.info("User %d liked message %s", user_id, message_key)

            elif action == "✅super_like":
                state_manager.set_message_rating(message_key, like_count, super_like_count + 1)
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
