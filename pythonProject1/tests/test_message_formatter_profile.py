import re
from unittest.mock import MagicMock

import pytest

from utils.message_formatter import MessageFormatter


@pytest.mark.asyncio
async def test_add_author_profile_block_inserts_profile_and_hash() -> None:
    formatter = MessageFormatter(bot=MagicMock())
    profile_text = "Имя: Анна\nВозраст: 28\nГород: Москва"

    text = await formatter.add_author_profile_block("<p>Основной текст</p>", profile_text)

    assert "Основной текст" in text
    assert "<blockquote>" in text
    assert "Имя: Анна" in text
    assert "<b>Хэш автора:</b>" in text
    _, author_hash = await formatter.extract_author_profile(text)
    assert author_hash is not None
    assert len(author_hash) == 64


@pytest.mark.asyncio
async def test_extract_author_profile_round_trip() -> None:
    formatter = MessageFormatter(bot=MagicMock())
    profile_text = "Профиль автора: разработчик, 30 лет"

    text = await formatter.add_author_profile_block("<p>Контент</p>", profile_text)
    restored_profile, restored_hash = await formatter.extract_author_profile(text)

    assert restored_profile == profile_text
    assert restored_hash is not None
    assert restored_hash == formatter.calculate_author_hash(profile_text)
