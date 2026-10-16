import pytest
from types import SimpleNamespace
from unittest.mock import patch

from services.vote_service import VoteService
from services.user_profile_service import user_profile_service
from state_manager import state_manager


class DummyBot:
    def __init__(self):
        self.sent = False

    async def send_message(self, *args, **kwargs):
        self.sent = True
        return None


class DummyMessageService:
    def __init__(self):
        self.bot = DummyBot()
        self.updated = False

    async def update_message_rating(self, *args, **kwargs):
        self.updated = True
        return None


@pytest.mark.asyncio
async def test_vote_blocked_if_profile_removed_before_apply():
    """Vote should be blocked if user's profile disappears between initial check and apply-time."""
    state_manager.reset()

    service = VoteService(DummyMessageService())

    message = SimpleNamespace(
        html_text='',
        text='',
        chat=SimpleNamespace(id=123),
        message_id=42,
    )

    callback = SimpleNamespace(
        from_user=SimpleNamespace(id=123, first_name="Alice"),
        data="✅like:-100:42",
        message=message,
    )

    # Simulate TOCTOU: first call -> True (has profile), second call -> False (profile gone)
    with patch.object(user_profile_service, 'has_profile', side_effect=[True, False]):
        await service.process(callback)

    rating = state_manager.get_message_rating("-100:42")
    # Like should NOT be incremented
    assert rating.like == 0
    # update_message_rating should not be called
    assert not service.message_service.updated
    # user should have been prompted to create profile
    assert service.message_service.bot.sent
