"""Tests for globally unique Telegram message keys."""

from datetime import datetime, timezone

from aiogram.types import Chat, Message

from utils.telegram_keys import message_key, telegram_message_key


def test_telegram_message_key_contains_chat_and_message_id() -> None:
    assert telegram_message_key(-100123, 42) == "-100123:42"


def test_message_key_uses_both_identifiers() -> None:
    message = Message(
        message_id=42,
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat=Chat(id=-100123, type="supergroup"),
    )
    assert message_key(message) == "-100123:42"
