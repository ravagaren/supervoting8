"""Keyboard builders used by questionnaire messages."""
from collections.abc import Mapping

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def keyboard_builder(
    questionnaire_evaluation: Mapping[str, int],
    message_id: str,
) -> InlineKeyboardBuilder:
    """Build the inline keyboard for a questionnaire."""
    del questionnaire_evaluation  # Counts are rendered in the message footer.
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="❣", callback_data=f"✅like:{message_id}"),
        types.InlineKeyboardButton(
            text="❤", callback_data=f"✅super_like:{message_id}"
        ),
    )
    builder.adjust(3)
    return builder


# Backwards-compatible alias for external callers. New code should use the
# correctly spelled ``keyboard_builder`` name.
keyborad_builder = keyboard_builder
