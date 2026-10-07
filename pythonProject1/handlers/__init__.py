"""Регистрация обработчиков и связывание зависимостей.

В этом модуле собраны общие функции инициализации обработчиков бота:

* ``configure_services`` передаёт необходимые сервисы обработчикам;
* ``register_all_handlers`` подключает маршрутизаторы к диспетчеру.

Сами правила обработки команд, сообщений и callback-запросов находятся в
отдельных модулях. Такое разделение позволяет не смешивать настройку бота с
реализацией бизнес-логики обработчиков.
"""
from aiogram import Dispatcher

from services.message_service import MessageService
from .callback_handler import configure as configure_callbacks, router as callback_router
from .message_handler import configure as configure_messages, router as message_router
from .command_handler import configure as configure_commands, router as command_router


def configure_services(message_service: MessageService) -> None:
    """Передать сервисы всем обработчикам, которым они необходимы.

    Параметры:
        message_service: Сервис для работы с сообщениями и связанной
            бизнес-логикой голосования.

    Обработчики хранят переданный сервис внутри своих модулей и используют его
    при получении новых сообщений или callback-запросов. Вызвать эту функцию
    нужно до начала обработки обновлений, иначе обработчик может не иметь
    доступа к настроенной зависимости.
    """
    # Обработчик обычных сообщений использует сервис для обработки входящих
    # сообщений пользователей и подготовки ответа.
    configure_messages(message_service)

    # Callback-обработчик получает тот же сервис через отдельную функцию
    # конфигурации и на его основе обрабатывает нажатия кнопок голосования.
    configure_callbacks(message_service)

    # Обработчик команд используется для создания анкеты через /create_short и /create_full.
    configure_commands(message_service)


def register_all_handlers(dispatcher: Dispatcher) -> None:
    """Зарегистрировать все маршрутизаторы в диспетчере aiogram.

    Параметры:
        dispatcher: Экземпляр ``Dispatcher``, который принимает обновления
            Telegram и передаёт их подходящим обработчикам.

    Порядок подключения определяет порядок, в котором aiogram проверяет
    маршрутизаторы. Здесь отдельно подключаются обработчики команд, обычных
    сообщений и callback-запросов от inline-кнопок.
    """
    # Команды (/start, /help и другие) регистрируются первыми, чтобы их
    # обработчики были явно отделены от общей обработки сообщений.
    dispatcher.include_router(command_router)

    # Этот маршрутизатор отвечает за обычные входящие сообщения пользователя,
    # например текст и фотографии.
    dispatcher.include_router(message_router)

    # Callback-маршрутизатор обрабатывает нажатия inline-кнопок голосования.
    dispatcher.include_router(callback_router)
