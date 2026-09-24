"""Keyboard builders used by questionnaire messages."""
from collections.abc import Mapping

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def keyboard_builder(
    questionnaire_evaluation: Mapping[str, int],
    message_key: str,
) -> InlineKeyboardBuilder:
    """Build the inline keyboard using a globally unique Telegram key."""
    del questionnaire_evaluation
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="❣", callback_data=f"✅like:{message_key}"),
        types.InlineKeyboardButton(
            text="❤", callback_data=f"✅super_like:{message_key}"
        ),
    )
    builder.adjust(3)
    return builder


keyborad_builder = keyboard_builder
