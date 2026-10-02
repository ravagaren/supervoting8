"""Форматирование и анализ текстов анкеты."""
from typing import Any

from aiogram.types import Message
from aiogram.utils.formatting import (
    Bold,
    ExpandableBlockQuote,
    HashTag,
    Text,
    TextLink,
    Url,
    as_line,
)

from keyboards.keyboard_builder import keyboard_builder
from my_types import AnalysisResult
from state_manager import state_manager
from utils.telegram_keys import message_key

DEFAULT_IMAGE_URL = "https://telegra.ph/file/94a1f3a5a8ec1e9e57597.jpg"
ZERO_WIDTH_SPACE = "\u200b"


async def generate_test_content_message(image_url: str | None = None, text_form: str | None = None) -> Text:
    """Генерирует HTML-структуру текста анкеты для отправки в Telegram.

    Используем невидимый символ вместо точки в начале ссылки, чтобы Telegram показывал
    превью изображения, но сам текст ссылки не отображался пользователю.
    """
    image_url = image_url or DEFAULT_IMAGE_URL
    hidden_link = TextLink(ZERO_WIDTH_SPACE, url=image_url)

    if text_form is None:
        return Text(
            as_line(hidden_link),
            as_line(Url("https://ift.tt/G2vJD1H")),
            as_line(HashTag("ж_верх "), HashTag("знакомства ")),
            as_line("1. Саша"), as_line("2. Леди"), as_line("3. #Москва"),
            ExpandableBlockQuote(
                as_line("4. свитч с уклоном вниз"),
                as_line("5.Ищу партнёра для сессионных отношений (цис-женщину, транс-мужчину Возраст: до 45 лет."),
                as_line("Фетиши: атлетизм и мускулистость, tomboy-style, андрогинность."),
                as_line("6А) БДСМ-super_like:"),
                as_line("Общее настроение экшенов: пытки, избиение гопниками, армейская дедовщина"),
                as_line("Б) Сексуальные super_like: возможно всё, но не сразу"),
                as_line("Подробнее - https://ift.tt/d1z4Sqs"),
                as_line("id::!12345678"), as_line("РАНГ: Серебрянный"),
                as_line("~`!@#$%^&*()_`123456788900-"),
            ),
        )

    hashtag_index = text_form.find("#не_см_flog_ru")
    if hashtag_index < 0:
        hashtag_index = len(text_form)
    split_at = hashtag_index + 150
    return Text(
        as_line(hidden_link),
        as_line(text_form[:split_at]),
        ExpandableBlockQuote(text_form[split_at:-1]),
        as_line(""),
    )


async def analysis_message_and_rating_calculation(
    from_user_id: int | None = None,
    message: Message | None = None,
    origin_message_id: str | None = None,
    local_user_ratings: dict[Any, Any] | None = None,
    local_message_ratings: dict[str, Any] | None = None,
) -> AnalysisResult:
    """Проверяет состояние сообщения и создаёт клавиатуру.

    Для новых сообщений ключ строится из ``chat.id`` и ``message_id``.
    ``origin_message_id`` оставлен для совместимости с legacy-вызовами.
    """
    del local_user_ratings, local_message_ratings
    if message is None:
        raise ValueError("message is required")
    user_id = from_user_id if from_user_id is not None else message.from_user.id
    current_key = origin_message_id or message_key(message)
    message_rating = state_manager.get_message_rating(current_key)
    state_manager.get_user_rating(user_id, current_key)
    builder = keyboard_builder(
        {"like": message_rating.like, "super_like": message_rating.super_like},
        current_key,
    )
    return AnalysisResult(
        builder=builder,
        origin_message_id=current_key,
        local_user_ratings=state_manager.get_all_user_ratings(),
        message_ratings=state_manager.get_all_message_ratings(),
    )
