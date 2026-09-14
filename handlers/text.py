from typing import Optional, List

from handlers.control_commands import router
from aiogram import F, types

from state_manager import state_manager
from utils.usefull_utils import analysis_message_and_rating_calculation, generate_test_content_message
from utils.refine_form_text import refine_form_text
from utils.message_builder import add_bottom_bar_encourages_clicking_buttons

# Локальный накопитель для уточнения анкеты (минимальный рефакторинг; позже вынести в state_manager)
summaru: List[str] = ["Анкета"]


@router.message(F.text)
async def add_bottom_and_buttons_from_text(
    message: types.Message,
    from_user_id_value: Optional[int] = None,
    origin_message_id_value: Optional[str] = None,
    from_user_first_name_value: str = "",
    local_dictionary_storing_user_ratings=None,
) -> None:
    global summaru

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

    text = getattr(message, "text", "") or ""

    # Накапливаем текст в summaru и уточняем его
    summaru.append(text)
    try:
        summaru = refine_form_text(summaru)
    except Exception:
        # Если refine не сработал — не прерываем обработку
        pass

    if not summaru:
        return

    image_anket_url: str = summaru[0]

    content = await generate_test_content_message(image_anket_url, text)
    content_html = content.as_html()

    final_html = add_bottom_bar_encourages_clicking_buttons(
        content_html, like_value, super_like_value, None, from_user_first_name_value
    )

    await message.answer(final_html, reply_markup=result.builder.as_markup())
