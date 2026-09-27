"""Подсчёт лайков и супер-лайков из HTML-текста сообщения."""

import re
from typing import Tuple


async def extract_likes_from_message_text(message_html_text: str) -> Tuple[int, int]:
    """Извлекает значения лайков и супер-лайков из HTML-содержимого анкеты.
    
    Ищет в тексте паттерны вроде:
    - "Отдай симпатию ❣ 5" или "Отдай лайк 💟 5"
    - "Отдай супер симпатию ❤ 2" или "Отдай супер лайк 🔥 2"
    
    Args:
        message_html_text: HTML-текст сообщения из Telegram
        
    Returns:
        Кортеж (likes, super_likes) с извлечёнными числами
    """
    like_value: int = 0
    super_like_value: int = 0

    # Ищем "Отдай симпатию ❣ 5" или "Отдай лайк 💟 5"
    like_match = re.search(r"Отдай\s+(?:лайк|симпатию)\s*(?:💟|❣)\s*(\d+)", message_html_text)
    if like_match:
        like_value = int(like_match.group(1))

    # Ищем "Отдай супер симпатию ❤ 2" или "Отдай супер лайк 🔥 2"
    super_like_match = re.search(
        r"Отдай\s+супер(?:\s+|-)(?:лайк|симпатию)\s*(?:🔥|❤)\s*(\d+)", message_html_text
    )
    if super_like_match:
        super_like_value = int(super_like_match.group(1))

    return like_value, super_like_value
