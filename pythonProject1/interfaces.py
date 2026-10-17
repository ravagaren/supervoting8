"""Типизированные контракты, используемые обработчиками и сервисами."""
from typing import Protocol

from aiogram import types
from aiogram.utils.formatting import Text


class MessageFormatterProtocol(Protocol):
    """Интерфейс для форматирования и отправки сообщений-анкеты.

    Этот протокол описывает, как следует форматировать сообщения перед отправкой
    в Telegram: рендерить контент, добавлять рейтинг владельца и прикреплять
    кнопки для голосования.
    """

    async def process_questionnaire_message(
        self,
        message: types.Message,
        content: Text,
        message_id: str,
        likes: int,
        super_likes: int,
        owner_rating: int,
        user_name: str = "",
        reply_markup: object | None = None,
    ) -> None:
        """Отправить или обновить сообщение-анкету с информацией о рейтинге.

        Аргументы:
            message: Исходный объект Telegram сообщения.
            content: Отформатированный текст сообщения.
            message_id: Уникальный ключ для этого сообщения (chat_id:message_id).
            likes: Текущее количество лайков.
            super_likes: Текущее количество супер-лайков.
            owner_rating: Рейтинг владельца, полученный из сервиса отпечатков.
            user_name: Имя автора сообщения.
            reply_markup: Inline-клавиатура с кнопками для голосования.
        """
        ...

    async def update_message_with_rating(
        self,
        message: types.Message,
        message_id: str,
        likes: int,
        super_likes: int,
        owner_rating: int,
        user_name: str,
        reply_markup: object | None = None,
    ) -> None:
        """Обновить рейтинг сообщения, не удаляя кнопки голосования.

        Этот метод вызывается, когда пользователь нажимает кнопку голосования.
        Он обновляет футер сообщения с новыми значениями рейтинга, сохраняя
        при этом клавиатуру без изменений.

        Аргументы:
            message: Объект Telegram сообщения для обновления.
            message_id: Уникальный ключ сообщения (chat_id:message_id).
            likes: Обновлённое число лайков.
            super_likes: Обновлённое число супер-лайков.
            owner_rating: Рейтинг владельца из сервиса отпечатков.
            user_name: Имя текущего голосующего.
            reply_markup: Inline-клавиатура, которую нужно сохранить.
        """
        ...
