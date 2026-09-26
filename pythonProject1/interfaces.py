"""Typed contracts shared by handlers and services."""
from typing import Protocol

from aiogram import types
from aiogram.utils.formatting import Text


class MessageFormatterProtocol(Protocol):
    """Interface for formatting and sending questionnaire messages.

    This protocol defines how messages should be formatted before sending to Telegram.
    It includes rendering the content, adding owner rating, and attaching voting buttons.
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
        """Send or update a questionnaire message with rating information.

        Args:
            message: Original Telegram message object.
            content: Formatted text content of the message.
            message_id: Unique key for this message (chat_id:message_id).
            likes: Current number of likes.
            super_likes: Current number of super likes.
            owner_rating: Owner reputation rating from fingerprint service.
            user_name: Name of the message author.
            reply_markup: Inline keyboard buttons for voting.
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
        """Update message rating without removing voting buttons.

        This method is called when a user clicks a voting button.
        It updates the message footer with new rating values without
        changing the keyboard.

        Args:
            message: Telegram message object to update.
            message_id: Unique key for this message (chat_id:message_id).
            likes: Updated number of likes.
            super_likes: Updated number of super likes.
            owner_rating: Owner reputation rating from fingerprint service.
            user_name: Name of the current voter.
            reply_markup: Inline keyboard buttons to preserve.
        """
        ...
