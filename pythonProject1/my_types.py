"""Typed result objects used by message analysis."""
from dataclasses import dataclass
from typing import Any

from aiogram.utils.keyboard import InlineKeyboardBuilder


@dataclass
class AnalysisResult:
    builder: InlineKeyboardBuilder
    origin_message_id: str
    local_user_ratings: dict[int, dict[str, dict[str, int]]]
    message_ratings: dict[str, Any]
