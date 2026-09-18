"""Application-level processing of questionnaire messages."""
import config
from aiogram import Bot, types

from state_manager import state_manager
from utils.imgbb import get_and_upload_photo_to_imgbb
from utils.refine_form_text import refine_form_text
from utils.usefull_utils import analysis_message_and_rating_calculation, generate_test_content_message


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
        file_info = await self.bot.get_file(photo.file_id)
        image_url = await get_and_upload_photo_to_imgbb(
            file_info.file_path, config.token, config.imgbb_api_key, session=self.http_session
        ) or photo.file_id
        content = await generate_test_content_message(image_url, getattr(message, "caption", None) or "")
        await self._ensure_formatter().process_questionnaire_message(
            message, content, result.origin_message_id, rating.like, rating.super_like,
            getattr(message.from_user, "first_name", ""), result.builder.as_markup()
        )

    async def update_message_rating(self, message: types.Message, message_id: str, user_name: str) -> None:
        rating = state_manager.get_message_rating(message_id)
        await self._ensure_formatter().update_message_with_rating(
            message, message_id, rating.like, rating.super_like, user_name
        )
