"""Точка входа запуска Telegram-бота.Test"""
import asyncio

from app import main


if __name__ == "__main__":
    # Запускаем асинхронный цикл основного приложения бота.
    asyncio.run(main())
