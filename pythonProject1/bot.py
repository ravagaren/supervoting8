"""Executable entry point for the Telegram bot.

Application wiring is implemented in :mod:`app`; this module intentionally
contains no compatibility handlers or module-level service state.
"""
import asyncio

from app import main


if __name__ == "__main__":
    asyncio.run(main())
