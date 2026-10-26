"""Приложение-level processing of questionnaire messages."""
import asyncio
import html
import logging
import random
import re
from typing import TYPE_CHECKING

import aiohttp
from aiogram import Bot, types
from aiogram.exceptions import TelegramBadRequest

import config
from interfaces import MessageFormatterProtocol
from keyboards.keyboard_builder import keyboard_builder
from services.author_profile_service import AuthorProfileService
from services.owner_fingerprint_service import RandomOwnerFingerprintService
from services.questionnaire_service import QuestionnaireType, questionnaire_service
from services.user_profile_service import user_profile_service
from state_manager import state_manager
from utils.imgbb import get_and_upload_photo_to_imgbb
from utils.refine_form_text import refine_form_text
from utils.useful_utils import (
    analysis_message_and_rating_calculation,
    generate_test_content_message,
)

if TYPE_CHECKING:
    from aiogram.utils.formatting import Text

logger = logging.getLogger(__name__)

DELETE_MESSAGE_DELAY = 10

PROFILE_REQUEST_PROMPT = (
    "У вас ещё нет заполненной анкеты.\n\n"
    "Отправьте в личное сообщение следующие данные через пробел:\n\n"
    "<b>ник возраст город позиция</b>\n\n"
    "Примеры:\n"
    "<code>Саша 28 Москва Специалист</code>\n"
    "<code>Анна 25 СПб Разработчик</code>\n\n"
    f"Чтобы заполнить анкету, откройте бота: <a href=\"{config.BOT_URL}\">{config.BOT_USERNAME}</a>\n\n"
    "После заполнения анкеты вы сможете взаимодействовать с ботом."
)


class MessageService:
    """Сервис обработки входящих сообщений с анализом владельца контента."""
