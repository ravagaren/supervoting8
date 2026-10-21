"""User profile service (in-memory only).

Redis-backed persistence was removed by decision; this project now uses SQLite
for durable data storage, while the runtime state remains in-memory.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """Профиль пользователя."""

    user_id: int
    nickname: str
    age: str
    city: str
    position: str
    created_at: datetime | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class UserProfileService:
    """Сервис для работы с профилями пользователей."""

    def __init__(self):
        self._profiles: dict[int, UserProfile] = {}

    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        """Получить профиль пользователя по ID (sync)."""
        return self._profiles.get(user_id)

    def create_from_text(self, user_id: int, text: str) -> Optional[UserProfile]:
        """Создать профиль из текста формата: ник возраст город позиция."""
        parts = text.strip().split()
        if len(parts) < 4:
            logger.warning("Invalid profile format for user %d: expected 4 parts, got %d", user_id, len(parts))
            return None

        nickname = parts[0]
        age = parts[1]
        city = parts[2]
        position = " ".join(parts[3:])

        profile = UserProfile(
            user_id=user_id,
            nickname=nickname,
            age=age,
            city=city,
            position=position,
        )

        self._profiles[user_id] = profile
        logger.info(
            "Created profile for user %d: nickname=%s, age=%s, city=%s, position=%s",
            user_id,
            nickname,
            age,
            city,
            position,
        )
        logger.info(
            "Profile found for user %d: nickname=%s, age=%s, city=%s, position=%s",
            user_id,
            nickname,
            age,
            city,
            position,
        )
        return profile

    def has_profile(self, user_id: int) -> bool:
        """Проверить, есть ли профиль у пользователя (sync)."""
        return user_id in self._profiles

    def reset(self) -> None:
        """Очистить все профили (для тестов)."""
        self._profiles.clear()

    async def has_profile_async(self, user_id: int) -> bool:
        """Async compatibility wrapper; currently memory-only, no Redis dependency."""
        return self.has_profile(user_id)

    async def get_by_user_id_async(self, user_id: int) -> Optional[UserProfile]:
        """Async compatibility wrapper; currently memory-only, no Redis dependency."""
        return self.get_by_user_id(user_id)


user_profile_service = UserProfileService()
