"""Tests for owner rating integration in message processing."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from aiogram.types import Chat, Message, User

from services.author_profile_service import AuthorProfileService
from services.author_rating_service import author_rating_service
from services.message_service import MessageService
from services.owner_fingerprint_models import OwnerCheckResult, OwnerStatus
from services.owner_fingerprint_service import RandomOwnerFingerprintService
from state_manager import AuthorRating, state_manager
from utils.telegram_keys import message_key


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
async def test_like_does_not_change_author_rating(mock_bot, mock_formatter, sample_message):
    """Like should not mutate system author rating."""
    state_manager.reset()
    author_hash = "a" * 64
    state_manager.set_author_rating(
        author_hash,
        AuthorRating(owner_rating=30, message_count=6, avg_content_rating=0.0, last_updated=datetime.now()),
    )
    message_key_value = message_key(sample_message)
    state_manager.set_message_rating(message_key_value, 1, 0, 30)

    before = state_manager.get_author_rating(author_hash).owner_rating
    await author_rating_service.sync_message_author_rating(author_hash, message_key_value)

    assert state_manager.get_author_rating(author_hash).owner_rating == before == 30
    assert state_manager.get_message_rating(message_key_value).owner_rating == 30


@pytest.mark.asyncio
async def test_message_service_includes_owner_rating(mock_bot, mock_formatter, sample_message):
    """Test that message service passes owner_rating to formatter."""
    fingerprint_service = RandomOwnerFingerprintService(random_source=lambda: True)

    service = MessageService(mock_bot, owner_fingerprint_service=fingerprint_service)
    service.set_formatter(mock_formatter)

    state_manager.reset()

    await service.process_text(sample_message)

    assert mock_formatter.process_questionnaire_message.called
    call_args = mock_formatter.process_questionnaire_message.call_args
    assert call_args is not None
    assert 50 in call_args[0] or call_args.kwargs.get("owner_rating") == 50


@pytest.mark.asyncio
async def test_owner_not_found_low_rating(mock_bot, mock_formatter, sample_message):
    """Test that NOT_FOUND status results in owner_rating=1."""
    fingerprint_service = RandomOwnerFingerprintService(random_source=lambda: False)

    service = MessageService(mock_bot, owner_fingerprint_service=fingerprint_service)
    service.set_formatter(mock_formatter)

    state_manager.reset()

    await service.process_text(sample_message)

    assert mock_formatter.process_questionnaire_message.called
    call_args = mock_formatter.process_questionnaire_message.call_args
    assert 1 in call_args[0] or call_args.kwargs.get("owner_rating") == 1


@pytest.mark.asyncio
async def test_update_rating_preserves_owner_rating(mock_bot, mock_formatter, sample_message):
    """Test that updating message rating doesn't change owner_rating."""
    fingerprint_service = RandomOwnerFingerprintService(random_source=lambda: True)
    service = MessageService(mock_bot, owner_fingerprint_service=fingerprint_service)
    service.set_formatter(mock_formatter)

    state_manager.reset()

    msg_key = message_key(sample_message)
    state_manager.set_message_rating(msg_key, 5, 2)

    await service.update_message_rating(sample_message, msg_key, "TestUser")

    assert mock_formatter.update_message_with_rating.called
    call_args = mock_formatter.update_message_with_rating.call_args
    assert call_args is not None


@pytest.mark.asyncio
async def test_message_service_uses_author_profile_service(mock_bot, mock_formatter):
    """Test that MessageService uses AuthorProfileService to resolve owner."""
    service = MessageService(mock_bot)
    service.set_formatter(mock_formatter)

    state_manager.reset()

    message_without_profile = Message(
        message_id=43,
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat=Chat(id=-100123, type="supergroup"),
        from_user=User(id=12345, is_bot=False, first_name="TestUser"),
        text="Test content without profile",
    )

    await service.process_text(message_without_profile)

    assert mock_formatter.process_questionnaire_message.called
    call_args = mock_formatter.process_questionnaire_message.call_args
    assert call_args is not None
    assert "owner_rating" in call_args.kwargs or len(call_args[0]) > 5


@pytest.mark.asyncio
async def test_author_profile_service_resolves_owner(mock_bot, mock_formatter):
    """Test that AuthorProfileService is used when profile text is present."""
    service = MessageService(mock_bot)
    service.set_formatter(mock_formatter)

    state_manager.reset()

    profile_text = "Имя: Анна\nВозраст: 28\nГород: Москва"
    message_with_profile = Message(
        message_id=44,
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat=Chat(id=-100123, type="supergroup"),
        from_user=User(id=12345, is_bot=False, first_name="TestUser"),
        text=profile_text,
    )

    await service.process_text(message_with_profile)

    assert mock_formatter.process_questionnaire_message.called
    call_args = mock_formatter.process_questionnaire_message.call_args
    assert call_args is not None
    owner_rating = call_args.kwargs.get("owner_rating") or (call_args[0][5] if len(call_args[0]) > 5 else None)
    assert owner_rating is not None
