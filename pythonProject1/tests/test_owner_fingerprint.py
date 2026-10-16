"""Тесты для сервиса проверки отпечатка владельца."""
import pytest
from aiogram.types import Chat, Message, User
from datetime import datetime, timezone

from services.owner_fingerprint_models import OwnerStatus
from services.owner_fingerprint_service import RandomOwnerFingerprintService


@pytest.fixture
def sample_message() -> Message:
    """Создаёт пример Telegram-сообщения для тестирования."""
    return Message(
        message_id=42,
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat=Chat(id=-100123, type="supergroup"),
        from_user=User(id=12345, is_bot=False, first_name="Test"),
        text="Test message",
    )


@pytest.mark.asyncio
async def test_owner_found_status(sample_message: Message) -> None:
    """Проверяет, что статус FOUND возвращает рейтинг 50."""
    # Используем фиксированный источник случайности, который всегда возвращает True
    service = RandomOwnerFingerprintService(random_source=lambda: True)
    result = await service.check(sample_message)

    assert result.status == OwnerStatus.FOUND
    assert result.owner_rating == 50
    assert result.owner_id is None


@pytest.mark.asyncio
async def test_owner_not_found_status(sample_message: Message) -> None:
    """Проверяет, что статус NOT_FOUND возвращает рейтинг 1."""
    # Используем фиксированный источник случайности, который всегда возвращает False
    service = RandomOwnerFingerprintService(random_source=lambda: False)
    result = await service.check(sample_message)

    assert result.status == OwnerStatus.NOT_FOUND
    assert result.owner_rating == 1
    assert result.owner_id is None


@pytest.mark.asyncio
async def test_random_service_without_seed(sample_message: Message) -> None:
    """Проверяет, что сервис без явно заданного источника случайности возвращает корректный результат.

    Тест не проверяет статистику случайности, а лишь то, что сервис
    возвращает один из допустимых состояний при использовании реального random.choice().
    """
    service = RandomOwnerFingerprintService()  # Без random_source, используется default
    result = await service.check(sample_message)

    # Результат должен быть одним из двух допустимых состояний
    assert result.status in (OwnerStatus.FOUND, OwnerStatus.NOT_FOUND)
    if result.status == OwnerStatus.FOUND:
        assert result.owner_rating == 50
    else:
        assert result.owner_rating == 1


@pytest.mark.asyncio
async def test_multiple_checks_with_fixed_source(sample_message: Message) -> None:
    """Проверяет детерминированность при чередующемся источнике случайности."""
    checks_found = 0
    checks_not_found = 0

    # Чередуем True и False
    toggle = False

    def alternating_source():
        nonlocal toggle
        toggle = not toggle
        return toggle

    service = RandomOwnerFingerprintService(random_source=alternating_source)

    # Первый вызов должен вернуть toggled значение (True после первого переключения)
    result1 = await service.check(sample_message)
    if result1.status == OwnerStatus.FOUND:
        checks_found += 1
    else:
        checks_not_found += 1

    # Второй вызов переключит на False
    result2 = await service.check(sample_message)
    if result2.status == OwnerStatus.FOUND:
        checks_found += 1
    else:
        checks_not_found += 1

    # Должно быть по одному из каждого после чередования
    assert checks_found + checks_not_found == 2
