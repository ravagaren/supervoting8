"""Регистрация обработчиков и связывание зависимостей."""
from aiogram import Dispatcher

from services.message_service import MessageService
from .callback_handler import configure as configure_callbacks, router as callback_router
from .message_handler import configure as configure_messages, router as message_router
from .command_handler import router as command_router


def configure_services(message_service: MessageService) -> None:
    """Подключить сервисы к каждому набору обработчиков."""
    configure_messages(message_service)
    configure_callbacks(message_service)


def register_all_handlers(dispatcher: Dispatcher) -> None:
    """Подключить все роутеры диспетчера."""
    dispatcher.include_router(command_router)
    dispatcher.include_router(message_router)
    dispatcher.include_router(callback_router)
