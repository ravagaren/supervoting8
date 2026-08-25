"""
Configuration management for the bot.

Loads configuration from environment variables.
Never hardcode secrets in this file!
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class ConfigError(Exception):
    """Raised when required configuration is missing."""
    pass


# ============ Telegram Bot Configuration ============
TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
if not TOKEN:
    raise ConfigError(
        "TELEGRAM_BOT_TOKEN not set. "
        "Please set it in .env file or as environment variable."
    )

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
