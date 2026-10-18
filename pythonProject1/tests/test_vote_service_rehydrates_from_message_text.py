import pytest
from types import SimpleNamespace
from unittest.mock import patch

from services.vote_service import VoteService
from services.user_profile_service import user_profile_service
from state_manager import state_manager

class DummyBot:
    async def send_message(self, *args, **kwargs):
        return None

class DummyMessageService:
    def __init__(self):
        self.bot = DummyBot()

    async def update_message_rating(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_like_rehydrates_from_message_text_before_increment():
    """If the voter has a profile, the service should rehydrate likes from message text and increment."""
    state_manager.reset()

    message = SimpleNamespace(
        html_text='... <b>Отдай симпатию ❣ 7</b> ...',
        text='... Отдай симпатию ❣ 7 ...',
        chat=SimpleNamespace(id=-1),
        message_id=42,
    )

    callback = SimpleNamespace(
        from_user=SimpleNamespace(id=123, first_name="Alice"),
        data="✅like:-100:42",
        message=message,
    )

    service = VoteService(DummyMessageService())
    state_manager.set_user_rating(123, "-100:42", {"like": 0, "super_like": 0})

    # Ensure voter is considered to have a profile (system policy: any action requires a profile)
    with patch.object(user_profile_service, 'has_profile', return_value=True):
        await service.process(callback)

    rating = state_manager.get_message_rating("-100:42")
    # Like should be incremented: initial 7 rehydrated + 1 -> 8
    assert rating.like == 8
