"""User profile service (in-memory only).

Redis-backed persistence was removed by decision; this project now uses SQLite
for durable data storage, while the runtime state remains in-memory.

SQLite check is intentionally stubbed out for now because the database is not
started and not part of the current runtime contract.
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
    """Сервис для работы с профилями пользователей.

    Memory-only implementation is the source of truth right now.
    SQLite-backed persistence is intentionally stubbed and not active until the
    database service is launched in the project runtime.
    """

    def __init__(self):
        self._profiles: dict[int, UserProfile] = {}
        self._sqlite_enabled = False

    def _sqlite_profile_exists(self, user_id: int) -> bool:
        """Placeholder for future SQLite validation.

        The database is not running yet, so this check is intentionally disabled.
        The application must behave as if SQLite was not available.
        """
        if not self._sqlite_enabled:
            logger.debug(
                "SQLite profile check is disabled for user %d; using in-memory profile state only",
                user_id,
            )
            return False

        # Future implementation would query SQLite here.
        # Example:
        #   with sqlite3.connect(DB_PATH) as conn:
        #       ...
        #   return bool(row)
        return False

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
        """Проверить, есть ли профиль у пользователя (sync).

        The only active source of truth is the in-memory registry. SQLite check is
        intentionally disabled until the storage layer is launched.
        """
        return user_id in self._profiles

    def reset(self) -> None:
        """Очистить все профили (для тестов)."""
        self._profiles.clear()

    async def has_profile_async(self, user_id: int) -> bool:
        """Async compatibility wrapper; currently memory-only, SQLite disabled."""
        if user_id in self._profiles:
            return True

        # Future SQLite check is intentionally disabled.
        return self._sqlite_profile_exists(user_id)

    async def get_by_user_id_async(self, user_id: int) -> Optional[UserProfile]:
        """Async compatibility wrapper; currently memory-only."""
        return self.get_by_user_id(user_id)


user_profile_service = UserProfileService()
