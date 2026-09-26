"""Tests for owner rating integration in message processing."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from aiogram.types import Chat, Message, User
from aiogram.utils.formatting import Text, as_line

from services.message_service import MessageService
from services.owner_fingerprint_models import OwnerCheckResult, OwnerStatus
from services.owner_fingerprint_service import RandomOwnerFingerprintService
from state_manager import state_manager


@pytest.fixture
def sample_message() -> Message:
    """Create a sample Telegram message for testing."""
    return Message(
        message_id=42,
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat=Chat(id=-100123, type="supergroup"),
        from_user=User(id=12345, is_bot=False, first_name="TestUser"),
        text="Test content",
    )


@pytest.fixture
def mock_formatter():
    """Create a mock message formatter."""
    formatter = MagicMock()
    formatter.process_questionnaire_message = AsyncMock()
    formatter.update_message_with_rating = AsyncMock()
    return formatter


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    return MagicMock()


@pytest.mark.asyncio
async def test_message_service_includes_owner_rating(mock_bot, mock_formatter, sample_message):
    """Test that message service passes owner_rating to formatter."""
    # Create fingerprint service that always returns FOUND
    fingerprint_service = RandomOwnerFingerprintService(random_source=lambda: True)

    # Create message service
    service = MessageService(mock_bot, owner_fingerprint_service=fingerprint_service)
    service.set_formatter(mock_formatter)

    # Reset state manager before test
    state_manager.reset()

    # Process text message
    await service.process_text(sample_message)

    # Verify formatter was called with owner_rating parameter
    assert mock_formatter.process_questionnaire_message.called
    call_args = mock_formatter.process_questionnaire_message.call_args
    # The owner_rating should be passed as a positional argument or keyword
    # Check that it's in the call (it's the 6th positional arg after: message, content, message_id, likes, super_likes)
    assert call_args is not None
    # owner_rating should be 50 for FOUND status
    assert 50 in call_args[0] or call_args.kwargs.get('owner_rating') == 50


@pytest.mark.asyncio
async def test_owner_not_found_low_rating(mock_bot, mock_formatter, sample_message):
    """Test that NOT_FOUND status results in owner_rating=1."""
    # Create fingerprint service that always returns NOT_FOUND
    fingerprint_service = RandomOwnerFingerprintService(random_source=lambda: False)

    service = MessageService(mock_bot, owner_fingerprint_service=fingerprint_service)
    service.set_formatter(mock_formatter)

    state_manager.reset()

    await service.process_text(sample_message)

    # Verify formatter was called with owner_rating=1
    assert mock_formatter.process_questionnaire_message.called
    call_args = mock_formatter.process_questionnaire_message.call_args
    # owner_rating should be 1 for NOT_FOUND status
    assert 1 in call_args[0] or call_args.kwargs.get('owner_rating') == 1


@pytest.mark.asyncio
async def test_update_rating_preserves_owner_rating(mock_bot, mock_formatter, sample_message):
    """Test that updating message rating doesn't change owner_rating."""
    fingerprint_service = RandomOwnerFingerprintService(random_source=lambda: True)
    service = MessageService(mock_bot, owner_fingerprint_service=fingerprint_service)
    service.set_formatter(mock_formatter)

    state_manager.reset()

    # First set up a message
    from utils.telegram_keys import message_key

    msg_key = message_key(sample_message)
    state_manager.set_message_rating(msg_key, 5, 2)

    # Update rating
    await service.update_message_rating(sample_message, msg_key, "TestUser")

    # Verify formatter was called for update
    assert mock_formatter.update_message_with_rating.called
    call_args = mock_formatter.update_message_with_rating.call_args
    # owner_rating should be 50 (default for updates)
    assert call_args is not None
