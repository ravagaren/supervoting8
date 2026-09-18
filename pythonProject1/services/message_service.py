"""Application-level processing of questionnaire messages."""
import logging

import config
from aiogram import Bot, types

from keyboards.keyboard_builder import keyborad_builder
from state_manager import state_manager
from utils.imgbb import get_and_upload_photo_to_imgbb
from utils.refine_form_text import refine_form_text
from utils.usefull_utils import analysis_message_and_rating_calculation, generate_test_content_message

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, bot: Bot, http_session=None):
        self.bot = bot
        self.http_session = http_session
        self.summaru = ["Анкета"]
        self.formatter = None

    def set_formatter(self, formatter) -> None:
        self.formatter = formatter

    def _ensure_formatter(self):
        if self.formatter is None:
            raise RuntimeError("MessageFormatter must be configured before processing messages")
        return self.formatter

    async def _analysis(self, message: types.Message):
        result = await analysis_message_and_rating_calculation(
            getattr(message.from_user, "id", None), message, None,
            state_manager.get_all_user_ratings(), state_manager.get_all_message_ratings()
        )
        return result, state_manager.get_message_rating(result.origin_message_id)

    async def process_text(self, message: types.Message) -> None:
        result, rating = await self._analysis(message)
        text = getattr(message, "text", None) or ""
        self.summaru.append(text)
        self.summaru = refine_form_text(self.summaru)
        if not self.summaru:
            return
        content = await generate_test_content_message(self.summaru[0], text)
        await self._ensure_formatter().process_questionnaire_message(
            message, content, result.origin_message_id, rating.like, rating.super_like,
            getattr(message.from_user, "first_name", ""), result.builder.as_markup()
        )

    async def process_photo(self, message: types.Message) -> None:
        result, rating = await self._analysis(message)
        photo = message.photo[-1]
        image_url = photo.file_id

        # The test bot and some Telegram API error responses can return False
        # instead of a File object. In that case file_path is unavailable, so
        # keep the Telegram file_id as a safe fallback and continue processing.
        try:
            file_info = await self.bot.get_file(photo.file_id)
            file_path = getattr(file_info, "file_path", None)
            if file_path:
                image_url = await get_and_upload_photo_to_imgbb(
                    file_path,
                    config.token,
                    config.imgbb_api_key,
                    session=self.http_session,
                ) or photo.file_id
            else:
                logger.warning(
                    "Telegram did not return a file path for photo %s; using file_id fallback",
                    photo.file_id,
                )
        except Exception:
            logger.exception("Could not upload photo %s; using file_id fallback", photo.file_id)

        content = await generate_test_content_message(
            image_url, getattr(message, "caption", None) or ""
        )
        await self._ensure_formatter().process_questionnaire_message(
            message, content, result.origin_message_id, rating.like, rating.super_like,
            getattr(message.from_user, "first_name", ""), result.builder.as_markup()
        )

    async def update_message_rating(self, message: types.Message, message_id: str, user_name: str) -> None:
        """Re-render the footer and preserve the inline voting keyboard."""
        rating = state_manager.get_message_rating(message_id)
        builder = await keyborad_builder(
            {"like": rating.like, "super_like": rating.super_like}, message_id
        )
        await self._ensure_formatter().update_message_with_rating(
            message, message_id, rating.like, rating.super_like, user_name,
            reply_markup=builder.as_markup()
        )
