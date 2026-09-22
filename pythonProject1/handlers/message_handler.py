"""Маршрутизаторы для текстовых и фото-сообщений."""
from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.types import ContentType, Message

if TYPE_CHECKING:
    from services.message_service import MessageService

router = Router()
_message_service: MessageService | None = None


def configure(service: MessageService) -> None:
    """Подключить сервис обработки сообщений в роутер."""
    global _message_service
    _message_service = service


@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message) -> None:
    """Перенаправляет входящее фото в сервис MessageService."""
    if _message_service is not None:
        await _message_service.process_photo(message)


@router.message(F.text)
async def handle_text(message: Message) -> None:
    """Перенаправляет входящий текст в сервис MessageService."""
    if _message_service is not None:
        await _message_service.process_text(message)
