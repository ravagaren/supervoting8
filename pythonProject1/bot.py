"""Backward-compatible bot module.

The application implementation lives in :mod:`app`.  The wrapper functions
below preserve the public API used by the legacy tests and integrations while
routing all work through ``MessageService``.
"""
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, types

from app import create_bot, main as _main, setup_dispatcher as _setup_dispatcher
from services.message_service import MessageService

# Kept for integrations that replace ``bot.bot`` with a test bot.
bot: Bot = create_bot()
_message_service: Optional[MessageService] = None


def setup_dispatcher(bot_instance: Bot, dispatcher: Dispatcher) -> None:
    """Configure routers and retain the configured service for compatibility."""
    global bot, _message_service
    bot = bot_instance
    _message_service = _setup_dispatcher(bot_instance, dispatcher)


async def add_bottom_and_buttons_from_photo(
    message: types.Message,
    from_user_id_value: Optional[int] = None,
    origin_message_id_value: Optional[str] = None,
    from_user_first_name_value: str = "",
    local_dictionary_storing_user_ratings: Optional[Dict] = None,
) -> None:
    """Legacy adapter for the former photo handler API."""
    service = _get_service()
    await service.process_photo(message)


async def add_bottom_and_buttons_from_text(
    message: types.Message,
    from_user_id_value: Optional[int] = None,
    origin_message_id_value: Optional[str] = None,
    from_user_first_name_value: str = "",
    local_dictionary_storing_user_ratings: Optional[Dict] = None,
) -> None:
    """Legacy adapter for the former text handler API."""
    service = _get_service()
    await service.process_text(message)


def _get_service() -> MessageService:
    if _message_service is None:
        # Direct calls from older integrations may happen before dispatcher
        # setup. Configure a standalone service without registering routers.
        from utils.message_formatter import MessageFormatter

        service = MessageService(bot)
        service.set_formatter(MessageFormatter(bot))
        return service
    return _message_service


async def main() -> None:
    await _main()


__all__ = [
    "bot",
    "main",
    "setup_dispatcher",
    "add_bottom_and_buttons_from_photo",
    "add_bottom_and_buttons_from_text",
]


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
