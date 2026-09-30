import re
from unittest.mock import MagicMock

import pytest

from utils.message_formatter import MessageFormatter


@pytest.mark.asyncio
async def test_add_author_profile_block_inserts_hash() -> None:
    formatter = MessageFormatter(bot=MagicMock())
    profile_text = "Имя: Анна\nВозраст: 28\nГород: Москва"

    text = await formatter.add_author_profile_block("<p>Основной текст</p>", profile_text)

    assert "Основной текст" in text
    assert "<b>Хэш автора:</b>" in text
    # Check that hash is 64 characters (SHA-256)
    hash_match = re.search(r"<b>Хэш автора:</b>\s+([a-f0-9]{64})", text)
    assert hash_match is not None
    author_hash = hash_match.group(1)
    assert len(author_hash) == 64


@pytest.mark.asyncio
async def test_calculate_author_hash_consistency() -> None:
    formatter = MessageFormatter(bot=MagicMock())
    profile_text = "Профиль автора: разработчик, 30 лет"

    # Calculate hash directly
    expected_hash = formatter.calculate_author_hash(profile_text)
    
    # Add profile block and extract hash from it
    text = await formatter.add_author_profile_block("<p>Контент</p>", profile_text)
    hash_match = re.search(r"<b>Хэш автора:</b>\s+([a-f0-9]{64})", text)
    
    assert hash_match is not None
    actual_hash = hash_match.group(1)
    assert actual_hash == expected_hash
