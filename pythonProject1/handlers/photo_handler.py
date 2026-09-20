"""Старый обработчик фото-сообщений; оставлен как legacy-способ."""
from aiogram import types

from bot import add_bottom_bar_encourages_clicking_buttons
from utils.usefull_utils import generate_test_content_message, analysis_message_and_rating_calculation


class PhotoHandler:
    """Обработчик фото-сообщений с добавлением текста и кнопок."""

    def __init__(self, options_4):
        # Настройки предпросмотра ссылок для Telegram.
        self.options_4 = options_4

    async def from_photo_add_bottom_and_buttons(
        self,
        message: types.Message,
        from_user_id_value: int = None,
        origin_message_id_value: str = None,
    ):
        """Генерирует и отправляет анкету на основе изображения."""
        builder, origin_message_id = await analysis_message_and_rating_calculation(
            from_user_id_value, message, origin_message_id_value
        )

        print("Position _ ", message.caption.find("_________________"))

        image_url = (
            "https://ravagaren.wordpress.com/wp-content/uploads/2023/03/photo_2023-08-19_11-36-11.jpg?w=640"
        )

        content = await generate_test_content_message(image_url, message.caption)

        print("content - ", content.as_html())

        if content.as_html().find("_________________") == -1:
            content_text = await add_bottom_bar_encourages_clicking_buttons(origin_message_id, content.as_html())

            print("content_text is", content_text)

            await message.answer(
                content_text,
                link_preview_options=self.options_4,
                reply_markup=builder.as_markup(),
            )
