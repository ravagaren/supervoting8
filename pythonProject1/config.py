"""
Configuration management for the bot.

Loads configuration from environment variables.
Never hardcode secrets in this file!
"""

import logging
import os
import sys
from typing import Optional

# Try to load .env file, but don't fail if python-dotenv is not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Allow running tests without python-dotenv installed initially
    pass


class ConfigError(Exception):
    """Raised when required configuration is missing."""
    pass


# Determine if we're running tests
def _is_running_tests() -> bool:
    """Check if pytest is running."""
    return 'pytest' in sys.modules or 'py.test' in sys.modules


# ============ Telegram Bot Configuration ============
TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')

# Don't raise during local development — warn instead and allow a placeholder in tests.
if not TOKEN and not _is_running_tests():
    logging.warning(
        "TELEGRAM_BOT_TOKEN not set. Please set it in .env file or as environment variable. "
        "The application will continue, but the bot will not be able to connect without a valid token."
    )

# Use a dummy token for testing if not set
if not TOKEN and _is_running_tests():
    TOKEN = 'test_token_12345:ABCDEFGHIJKLMNOP'

# Backwards-compatible lowercase alias expected by other modules (`config.token`)
token: str = TOKEN

# ============ Channel and Chat Configuration ============
CHANNEL_NAME: str = os.getenv('CHANNEL_NAME', '@club2_service_dating')
INNER_CHAT_ID: str = os.getenv('INNER_CHAT_ID', '-1001342417108')
TEST_INNER_CHAT_ID: str = os.getenv('TEST_INNER_CHAT_ID', '-1001289319696')

# ============ Admin Chat IDs ============
ADMIN_CHAT_ID: str = os.getenv('ADMIN_CHAT_ID', '1048344056')
ADMIN_CHAT_ID_1: str = os.getenv('ADMIN_CHAT_ID_1', '946268326')
ADMIN_CHAT_ID_2: str = os.getenv('ADMIN_CHAT_ID_2', '6171415130')

# ============ Storage Configuration ============
CHANNEL_STORAGE_ANKET: str = os.getenv('CHANNEL_STORAGE_ANKET', '-1002186755449')

# ============ Message Thread Configuration ============
MESSAGE_THREAD_ID: int = int(os.getenv('MESSAGE_THREAD_ID', '1989'))
TEST_MESSAGE_THREAD_ID: int = int(os.getenv('TEST_MESSAGE_THREAD_ID', '956'))
# imgbb API настройки
imgbb_api_key = "bebdbb786bf41adc0e9855d945230950"  # Получить на https://imgbb.com/api