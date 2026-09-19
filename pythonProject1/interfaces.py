"""Typed contracts shared by handlers and services."""
from typing import Protocol

from aiogram import types
from aiogram.utils.formatting import Text


class MessageFormatterProtocol(Protocol):
    async def process_questionnaire_message(
        self,
        message: types.Message,
        content: Text,
        message_id: str,
        likes: int,
        super_likes: int,
        user_name: str = "",
        reply_markup: object | None = None,
    ) -> None: ...

    async def update_message_with_rating(
        self,
        message: types.Message,
        message_id: str,
        likes: int,
        super_likes: int,
        user_name: str,
        reply_markup: object | None = None,
    ) -> None: ...
