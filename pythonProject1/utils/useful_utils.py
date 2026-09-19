"""Formatting and questionnaire-analysis utilities."""
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

DEFAULT_IMAGE_URL = "https://telegra.ph/file/94a1f3a5a8ec1e9e57597.jpg"


async def generate_test_content_message(
    image_url: str | None = None,
    text_form: str | None = None,
) -> Text:
    """Generate formatted content for a questionnaire message."""
    image_url = image_url or DEFAULT_IMAGE_URL
    if text_form is None:
        return Text(
            as_line(TextLink(".", url=image_url)),
            as_line(Url("https://ift.tt/G2vJD1H")),
            as_line(HashTag("ж_верх "), HashTag("знакомства ")),
            as_line("1. Саша"),
            as_line("2. Леди"),
            as_line("3. #Москва"),
            ExpandableBlockQuote(
                as_line(Bold("Раскрыть ⬇⬇⬇")),
                as_line("4. свитч с уклоном вниз"),
                as_line(
                    "5.Ищу партнёра для сессионных отношений "
                    "(цис-женщину, транс-мужчину Возраст: до 45 лет."
                ),
                as_line(
                    "Фетиши: атлетизм и мускулистость, tomboy-style, андрогинность. "
                    "Не обязательно быть профи-спортсменом, но хотя бы минимальная "
                    "физическая развитость должна быть. Особая любовь к женщинам, "
                    "которые занимаются единоборствами"
                ),
                as_line("6А) БДСМ-super_like:"),
                as_line(
                    "Общее настроение экшенов: пытки, избиение гопниками, армейская "
                    "дедовщина, любое стихийное желание причинить боль"
                ),
                as_line(
                    "Б) Сексуальные super_like: возможно всё, но не сразу, "
                    "а по мере установления доверия"
                ),
                as_line("Подробнее - https://ift.tt/d1z4Sqs"),
                as_line("id::!12345678"),
                as_line("РАНГ: Серебрянный"),
                as_line("~`!@#$%^&*()_`123456788900-"),
            ),
        )

    hashtag_index = text_form.find("#не_см_flog_ru")
    if hashtag_index < 0:
        hashtag_index = len(text_form)
    split_at = hashtag_index + 150
    return Text(
        as_line(TextLink(".", url=image_url)),
        as_line(text_form[:split_at]),
        as_line(Bold("Раскрыть ⬇⬇⬇")),
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
    """Analyze a message and build a keyboard using the centralized state."""
    del local_user_ratings, local_message_ratings
    if message is None:
        raise ValueError("message is required")
    user_id = from_user_id if from_user_id is not None else message.from_user.id
    message_id = origin_message_id or str(message.message_id)
    message_rating = state_manager.get_message_rating(message_id)
    state_manager.get_user_rating(user_id, message_id)
    builder = keyboard_builder(
        {"like": message_rating.like, "super_like": message_rating.super_like},
        message_id,
    )
    return AnalysisResult(
        builder=builder,
        origin_message_id=message_id,
        local_user_ratings=state_manager.get_all_user_ratings(),
        message_ratings=state_manager.get_all_message_ratings(),
    )
