"""
Application entry point for the Telegram bot.

This module provides a clean, focused main() function that orchestrates
bot initialization and lifecycle management. All configuration and factory
logic has been delegated to dedicated modules.
"""

import asyncio
import logging
from typing import Optional

import aiohttp
from aiogram import Bot, Dispatcher

from bot.factory import BotFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BotApplication:
    """Manages the bot application lifecycle."""

    def __init__(self):
        """Initialize application state."""
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
        self.http_session: Optional[aiohttp.ClientSession] = None

    async def startup(self) -> None:
        """
        Initialize and start the bot application.

        Creates bot, dispatcher, and HTTP session, then starts polling.
        """
        logger.info("Starting bot application...")

        try:
            # Create bot and dispatcher using factory
            self.bot = BotFactory.create_bot()
            self.dispatcher = BotFactory.create_dispatcher()

            # Configure dispatcher with all handlers
            BotFactory.setup_dispatcher(self.dispatcher)

            # Create HTTP session for external API calls
            self.http_session = await BotFactory.create_http_session()

            logger.info("Bot initialized successfully")
            logger.info("Starting polling...")

            # Start polling for updates
            await self.dispatcher.start_polling(self.bot)

        except Exception as e:
            logger.error(f"Error during bot startup: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """
        Gracefully shut down the bot application.

        Closes HTTP session and bot session.
        """
        logger.info("Shutting down bot application...")

        try:
            if self.http_session is not None:
                await self.http_session.close()
                logger.info("HTTP session closed")

            if self.bot is not None:
                await self.bot.session.close()
                logger.info("Bot session closed")

            logger.info("Bot application shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)


async def main() -> None:
    """
    Main entry point for the application.

    Creates and runs the bot application.
    """
    app = BotApplication()
    await app.startup()


if __name__ == "__main__":
    asyncio.run(main())
