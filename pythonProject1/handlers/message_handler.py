from aiogram import F, Router
from aiogram.types import ContentType, Message

router = Router()
_message_service = None


def configure(service) -> None:
    global _message_service
    _message_service = service


@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message) -> None:
    if _message_service is not None:
        await _message_service.process_photo(message)


@router.message(F.text)
async def handle_text(message: Message) -> None:
    if _message_service is not None:
        await _message_service.process_text(message)
