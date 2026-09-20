"""Типизированные результаты анализа сообщений."""
from dataclasses import dataclass
from typing import Any

from aiogram.utils.keyboard import InlineKeyboardBuilder


@dataclass
class AnalysisResult:
    """Результат анализа: клавиатура, идентификатор и снимки рейтингов."""

    # Клавиатура с действиями голосования для анкеты.
    builder: InlineKeyboardBuilder
    # Идентификатор исходного сообщения анкеты.
    origin_message_id: str
    # Рейтинги пользователей в совместимом словарном формате.
    local_user_ratings: dict[int, dict[str, dict[str, int]]]
    # Общие рейтинги сообщений; тип значения зависит от хранилища состояния.
    message_ratings: dict[str, Any]
