"""Сервис проверки владельца контента по цифровому отпечатку.

Модуль предоставляет интерфейс для проверки, принадлежит ли содержимое
Telegram-сообщения идентифицированному владельцу. В MVP реализован заглушечный
вариант на основе случайного выбора, который имитирует поведение проверки
по базе отпечатков.

В будущих реализациях заглушку можно заменить реальным анализом отпечатка:
- Криптографические подписи
- Модели машинного обучения
- Проверка в блокчейне
- Сторонние сервисы идентификации
"""
import logging
import random
from typing import Callable, Optional

from aiogram.types import Message

from services.owner_fingerprint_models import OwnerCheckResult, OwnerStatus

logger = logging.getLogger(__name__)


class OwnerFingerprintService:
    """Интерфейс для проверки владельца Telegram-сообщения по цифровому отпечатку.

    Сервис абстрагирует логику определения того, принадлежит ли содержимое
    сообщения известному владельцу. В MVP используется рандомизированное поведение
    для тестирования сценариев.
    """

    async def check(self, message: Message) -> OwnerCheckResult:
        """Проверить, принадлежит ли содержимое сообщения идентифицированному владельцу.

        Аргументы:
            message: Telegram-сообщение для анализа.

        Возвращает:
            OwnerCheckResult со статусом и owner_rating.
            В заглушке MVP:
            - 50% вероятность статуса FOUND с owner_rating=50
            - 50% вероятность статуса NOT_FOUND с owner_rating=1
        """
        raise NotImplementedError("Subclasses must implement check()")


class RandomOwnerFingerprintService(OwnerFingerprintService):
    """MVP-реализация, использующая случайную заглушку для тестирования.

    Сервис симулирует два возможных результата с равной вероятностью:
    1. Владелец найден: owner_rating = 50 (высокая репутация)
    2. Владелец не найден: owner_rating = 1 (минимальная репутация)

    Рандомизация может контролироваться опциональным callable для тестов.
    """

    def __init__(self, random_source: Optional[Callable[[], bool]] = None):
        """Инициализировать сервис с опциональным источником случайности.

        Аргументы:
            random_source: Опциональный callable, возвращающий True/False для
                           статуса "владелец найден". Если None, используется
                           random.choice() с равной вероятностью. Удобно для
                           детерминированного тестирования.
        """
        self._random_source = random_source

    async def check(self, message: Message) -> OwnerCheckResult:
        """Проверить статус владельца случайным образом.

        Аргументы:
            message: Telegram-сообщение (в заглушке не используется, но оставлено
                     для совместимости интерфейса).

        Возвращает:
            OwnerCheckResult с случайным статусом и соответствующим owner_rating.
        """
        # Используем кастомный источник случайности для тестов, иначе random.choice()
        if self._random_source is not None:
            owner_found = self._random_source()
        else:
            owner_found = random.choice([True, False])

        if owner_found:
            logger.debug(
                "Owner fingerprint check: FOUND for message_id=%d from user_id=%s",
                message.message_id,
                message.from_user.id,
            )
            return OwnerCheckResult(
                status=OwnerStatus.FOUND,
                owner_rating=50,
                owner_id=None,
            )
        else:
            logger.debug(
                "Owner fingerprint check: NOT_FOUND for message_id=%d from user_id=%s",
                message.message_id,
                message.from_user.id,
            )
            return OwnerCheckResult(
                status=OwnerStatus.NOT_FOUND,
                owner_rating=1,
                owner_id=None,
            )
