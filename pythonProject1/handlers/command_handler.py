"""Обработчики команд бота /start и /test."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import LinkPreviewOptions, Message

from services.message_service import MessageService
from services.questionnaire_service import QuestionnaireType
from utils.useful_utils import generate_test_content_message

router = Router()
options_4 = LinkPreviewOptions(prefer_large_media=True, show_above_text=True)

_message_service: MessageService | None = None


def configure(service: MessageService) -> None:
    """Подключить сервис обработки сообщений в роутер."""
    global _message_service
    _message_service = service


@router.message(Command("start", ignore_case=True))
async def start(message: Message) -> None:
    """Команда запуска: информирует пользователя о доступной команде теста."""
    await message.answer("Use /Test")


@router.message(Command("test", ignore_case=True))
async def test(message: Message) -> None:
    """Создаёт пример анкеты и отправляет её пользователю."""
    content = await generate_test_content_message()
    await message.answer(**content.as_kwargs(), link_preview_options=options_4)


@router.message(Command("create_short", ignore_case=True))
async def create_short(message: Message) -> None:
    """Создаёт и сохраняет сокращённую анкету в storage chat с обязательными полями.

    Обязательные поля:
    - Пол: сгенерирован случайно из списка
    - Возраст: сгенерирован случайно из диапазонов
    - Адрес: сгенерирован случайно из списка городов
    - Позиционирование: сгенерирован случайно из профессий

    User ID сохраняется из сообщения пользователя.
    Сохраняется в чат, указанный в config.QUESTIONNAIRE_STORAGE_CHAT_ID
    """
    if _message_service is None:
        await message.answer("Сервис анкеты не инициализирован.")
        return

    await _message_service.create_manual_questionnaire(
        message=message,
        questionnaire_type=QuestionnaireType.SHORT,
    )
    await message.answer("✅ Сокращённая анкета создана и сохранена в хранилище.")


@router.message(Command("create_full", ignore_case=True))
async def create_full(message: Message) -> None:
    """Создаёт и сохраняет полную анкету в storage chat.

    Аналогично create_short, но для полной версии анкеты.
    Все поля генерируются из определённых диапазонов в MVP режиме.
    """
    if _message_service is None:
        await message.answer("Сервис анкеты не инициализирован.")
        return

    await _message_service.create_manual_questionnaire(
        message=message,
        questionnaire_type=QuestionnaireType.FULL,
    )
    await message.answer("✅ Полная анкета создана и сохранена в хранилище.")
