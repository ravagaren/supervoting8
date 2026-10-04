"""Управление настройками бота и окружением."""

import logging
import os
import sys

# Пытаемся загрузить .env при наличии python-dotenv.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # В тестах и локальной разработке отсутствие пакета допустимо.
    pass


class ConfigError(Exception):
    """Выбрасывается, когда обязательная конфигурация отсутствует."""

    pass


def _is_running_tests() -> bool:
    """Проверяет, запущены ли тесты pytest."""
    return "pytest" in sys.modules or "py.test" in sys.modules


# ============ Конфигурация Telegram-бота ============
TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

if not TOKEN and not _is_running_tests():
    logging.warning(
        "TELEGRAM_BOT_TOKEN not set. Please set it in .env file or as environment variable. "
        "The application will continue, but the bot will not be able to connect without a valid token."
    )

# Для тестов создаём фиктивный токен, чтобы код не падал при импорте.
if not TOKEN and _is_running_tests():
    TOKEN = "test_token_12345:ABCDEFGHIJKLMNOP"

# Совместимый alias для старого имени переменной.
token: str = TOKEN

# ============ Каналы и чаты ============
CHANNEL_NAME: str = os.getenv("CHANNEL_NAME", "@club2_service_dating")
INNER_CHAT_ID: str = os.getenv("INNER_CHAT_ID", "-1001342417108")
TEST_INNER_CHAT_ID: str = os.getenv("TEST_INNER_CHAT_ID", "-1001289319696")

# ============ ID администраторов ============
ADMIN_CHAT_ID: str = os.getenv("ADMIN_CHAT_ID", "1048344056")
ADMIN_CHAT_ID_1: str = os.getenv("ADMIN_CHAT_ID_1", "946268326")
ADMIN_CHAT_ID_2: str = os.getenv("ADMIN_CHAT_ID_2", "6171415130")

# ============ Хранилище анкет ============
CHANNEL_STORAGE_ANKET: str = os.getenv("CHANNEL_STORAGE_ANKET", "-1002186755449")
QUESTIONNAIRE_STORAGE_CHAT_ID: int = int(os.getenv("QUESTIONNAIRE_STORAGE_CHAT_ID", CHANNEL_STORAGE_ANKET))

# ============ Настройки ветки сообщений ============
MESSAGE_THREAD_ID: int = int(os.getenv("MESSAGE_THREAD_ID", "1989"))
TEST_MESSAGE_THREAD_ID: int = int(os.getenv("TEST_MESSAGE_THREAD_ID", "956"))
QUESTIONNAIRE_STORAGE_THREAD_ID: int = int(os.getenv("QUESTIONNAIRE_STORAGE_THREAD_ID", MESSAGE_THREAD_ID))

# Настройки доступа к imgbb.
imgbb_api_key = "bebdbb786bf41adc0e9855d945230950"  # Получить на https://imgbb.com/api

# ============ Тестовый профиль пользователя ============
TEST_USER_PROFILE: str = """#ж_верх #знакомства\n1. Саша\n2. Леди\n3. #Москва\n4. свитч с уклоном вниз\n5. Ищу партнёра для сессионных отношений (цис-женщину, транс-мужчину Возраст: до 45 лет.\nФетиши: атлетизм и мускулистость, tomboy-style, андрогинность.\n6А) БДСМ-super_like:\nОбщее настроение экшенов: пытки, избиение гопниками, армейская дедовщина\nБ) Сексуальные super_like: возможно всё, но не сразу\nПодробнее - https://ift.tt/d1z4Sqs\nid::!12345678\nРАНГ: Серебрянный\n~`!@#$%^&*()_`123456788900-"""
