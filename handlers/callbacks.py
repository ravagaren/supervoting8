from handlers.control_commands import router
from aiogram import F, types

from state_manager import state_manager
from utils.like_counter import like_counter
from utils.message_builder import add_bottom_bar_encourages_clicking_buttons

CALLBACK_LIKE_ACTION = "✅like"
CALLBACK_SUPER_LIKE_ACTION = "✅super_like"
INITIAL_RATING_TEXT = "Рейтинг анкеты(0.0)"
ERROR_SUPER_LIKE_UNAVAILABLE = "Супер симпатия пока недоступна"


@router.callback_query(F.data.startswith("✅"))
async def callbacks_calculation_of_likes(callback: types.CallbackQuery) -> None:
    parts = callback.data.split(":", 1)
    if len(parts) != 2:
        await callback.answer("Неверные данные", show_alert=True)
        return

    action, questionnaire_message_id = parts

    message_rating = state_manager.get_message_rating(questionnaire_message_id)
    like_value = message_rating.like
    super_like_value = message_rating.super_like

    cb_html: str = getattr(callback.message, "html_text", "") or ""
    if cb_html.find(INITIAL_RATING_TEXT) == -1 and like_value == 0 and super_like_value == 0:
        like_value, super_like_value = await like_counter(questionnaire_message_id, cb_html)
        state_manager.set_message_rating(questionnaire_message_id, like_value, super_like_value)

    if action == CALLBACK_LIKE_ACTION:
        state_manager.increment_message_like(questionnaire_message_id)
        state_manager.increment_user_like(callback.from_user.id, questionnaire_message_id)
        try:
            await callback.answer()
        except Exception:
            pass
    elif action == CALLBACK_SUPER_LIKE_ACTION:
        if state_manager.has_user_voted_super_like(callback.from_user.id, questionnaire_message_id):
            await callback.answer(text=ERROR_SUPER_LIKE_UNAVAILABLE, show_alert=True)
            return
        state_manager.increment_message_super_like(questionnaire_message_id)
        state_manager.increment_user_super_like(callback.from_user.id, questionnaire_message_id)
        try:
            await callback.answer()
        except Exception:
            pass
    else:
        await callback.answer("Неизвестное действие", show_alert=True)
        return

    # Перестроим текст сообщения и обновим
    updated_rating = state_manager.get_message_rating(questionnaire_message_id)
    common_text = (getattr(callback.message, "html_text", "") or "").split("_________________")[0]
    final_html = add_bottom_bar_encourages_clicking_buttons(common_text, updated_rating.like, updated_rating.super_like)

    try:
        await callback.message.edit_text(final_html, reply_markup=callback.message.reply_markup)
    except Exception:
        # Игнорируем возможные ошибки редактирования (например, если сообщение изменилось)
        pass
