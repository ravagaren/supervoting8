from aiogram import Dispatcher
from .command_handler import router as command_router
from .message_handler import router as message_router, configure as configure_messages
from .callback_handler import router as callback_router, configure as configure_callbacks


def configure_services(message_service) -> None:
    configure_messages(message_service)
    configure_callbacks(message_service)


def register_all_handlers(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(command_router)
    dispatcher.include_router(message_router)
    dispatcher.include_router(callback_router)
