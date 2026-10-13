import pytest
from types import SimpleNamespace

from services.vote_service import VoteService
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
    state_manager.set_user_rating(123, "-100:42", {"like": 0, "super_like": 0})  # если нужен отдельный метод
    # если у вас пользовательская запись не нужна — можно пропустить

    await service.process(callback)

    rating = state_manager.get_message_rating("-100:42")
    assert rating.like == 8