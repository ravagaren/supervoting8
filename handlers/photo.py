from typing import Optional

from handlers.control_commands import router
from aiogram import F, types
from aiogram.types import ContentType

from state_manager import state_manager
from utils.usefull_utils import analysis_message_and_rating_calculation, generate_test_content_message
from utils.imgbb import get_and_upload_photo_to_imgbb
from utils.message_builder import add_bottom_bar_encourages_clicking_buttons

import config


@router.message(F.content_type == ContentType.PHOTO)
async def add_bottom_and_buttons_from_photo(
    message: types.Message,
    from_user_id_value: Optional[int] = None,
    origin_message_id_value: Optional[str] = None,
    from_user_first_name_value: str = '',
    local_dictionary_storing_user_ratings=None,
    session: Optional[object] = None,
) -> None:
    result = await analysis_message_and_rating_calculation(
        from_user_id_value,
        message,
        origin_message_id_value,
        local_dictionary_storing_user_ratings,
        state_manager.get_all_message_ratings(),
    )

    if not result or not result.origin_message_id:
        return

    message_rating = state_manager.get_message_rating(result.origin_message_id)
    like_value = message_rating.like
    super_like_value = message_rating.super_like

    caption: str = getattr(message, "caption", "") or ""

    # Берём лучшее фото
    photo = message.photo[-1]
    file_info = await message.bot.get_file(photo.file_id)

    # Загружаем на imgbb (если не настроено — вернёт None)
    image_url = await get_and_upload_photo_to_imgbb(
        file_info.file_path, config.token, config.imgbb_api_key, session=session
    )
    if not image_url:
        image_url = photo.file_id

    content = await generate_test_content_message(image_url, caption)
    content_html = content.as_html()

    final_html = add_bottom_bar_encourages_clicking_buttons(
        content_html, like_value, super_like_value, None, from_user_first_name_value
    )

    await message.answer(final_html, reply_markup=result.builder.as_markup())
