"""Helpers for building stable Telegram message keys."""

from aiogram.types import Message


def telegram_message_key(chat_id: int, message_id: int) -> str:
    """Return a globally unambiguous key for a Telegram message.

    ``message_id`` is only unique within a chat, therefore all state that is
    associated with a Telegram message must use both identifiers.
    """
    return f"{chat_id}:{message_id}"


def message_key(message: Message) -> str:
    """Build a Telegram key from an aiogram message."""
    return telegram_message_key(message.chat.id, message.message_id)
