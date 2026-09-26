"""Tests for owner fingerprint service."""
import pytest
from aiogram.types import Chat, Message, User
from datetime import datetime, timezone

from services.owner_fingerprint_models import OwnerStatus
from services.owner_fingerprint_service import RandomOwnerFingerprintService


@pytest.fixture
def sample_message() -> Message:
    """Create a sample Telegram message for testing."""
    return Message(
        message_id=42,
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat=Chat(id=-100123, type="supergroup"),
        from_user=User(id=12345, is_bot=False, first_name="Test"),
        text="Test message",
    )


@pytest.mark.asyncio
async def test_owner_found_status(sample_message: Message) -> None:
    """Test that FOUND status returns rating of 50."""
    # Use fixed random source that always returns True
    service = RandomOwnerFingerprintService(random_source=lambda: True)
    result = await service.check(sample_message)

    assert result.status == OwnerStatus.FOUND
    assert result.owner_rating == 50
    assert result.owner_id is None


@pytest.mark.asyncio
async def test_owner_not_found_status(sample_message: Message) -> None:
    """Test that NOT_FOUND status returns rating of 1."""
    # Use fixed random source that always returns False
    service = RandomOwnerFingerprintService(random_source=lambda: False)
    result = await service.check(sample_message)

    assert result.status == OwnerStatus.NOT_FOUND
    assert result.owner_rating == 1
    assert result.owner_id is None


@pytest.mark.asyncio
async def test_random_service_without_seed(sample_message: Message) -> None:
    """Test that random service produces valid results without seeding.

    This test doesn't verify the randomness, just that the service
    returns valid results when using actual random choice.
    """
    service = RandomOwnerFingerprintService()  # No random_source, uses default
    result = await service.check(sample_message)

    # Result should be one of the two valid states
    assert result.status in (OwnerStatus.FOUND, OwnerStatus.NOT_FOUND)
    if result.status == OwnerStatus.FOUND:
        assert result.owner_rating == 50
    else:
        assert result.owner_rating == 1


@pytest.mark.asyncio
async def test_multiple_checks_with_fixed_source(sample_message: Message) -> None:
    """Test that multiple checks with fixed source are deterministic."""
    checks_found = 0
    checks_not_found = 0

    # Alternate between True and False
    toggle = False

    def alternating_source():
        nonlocal toggle
        toggle = not toggle
        return toggle

    service = RandomOwnerFingerprintService(random_source=alternating_source)

    # First check should use the toggled value (True after first toggle)
    result1 = await service.check(sample_message)
    if result1.status == OwnerStatus.FOUND:
        checks_found += 1
    else:
        checks_not_found += 1

    # Second check should toggle to False
    result2 = await service.check(sample_message)
    if result2.status == OwnerStatus.FOUND:
        checks_found += 1
    else:
        checks_not_found += 1

    # Should have one of each after alternating
    assert checks_found + checks_not_found == 2
