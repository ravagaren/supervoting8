"""Те��ты для формирования ответов bot-команд."""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from handlers.control_commands import generate_test_message, options_4


@pytest.mark.asyncio
@patch("bot.generate_test_content_message", new_callable=AsyncMock)
async def test_generate_test_message_stub(mock_generate):
    """Проверяет, что команда /test вызывает генерацию текста и ответ пользователю."""
    global options_4

    mock_content = Mock()
    mock_content.as_kwargs.return_value = {"text": "Stub message"}
    mock_generate.return_value = mock_content

    message = Mock()
    message.answer = AsyncMock()

    await generate_test_message(message)

    mock_generate.assert_called_once()
    message.answer.assert_awaited_once()
    message.answer.assert_awaited_with(text="Stub message", link_preview_options=options_4)
