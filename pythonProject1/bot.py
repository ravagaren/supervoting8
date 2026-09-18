"""Backward-compatible entry point.

The implementation now lives in :mod:`app`; this module deliberately contains
no handlers or business logic. Run ``python app.py`` (or this module) to start
polling.
"""
from app import create_bot, main, setup_dispatcher

bot = create_bot()

__all__ = ["bot", "create_bot", "setup_dispatcher", "main"]


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
