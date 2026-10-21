"""User profile service (in-memory only).

Redis-backed persistence was removed by decision; this project now uses SQLite
for durable data storage, while the runtime state remains in-memory.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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
        self._storage_path = Path(__file__).resolve().parent.parent / "data" / "user_profiles.json"
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load persisted profiles created before the process restart."""
        if not self._storage_path.exists():
            return

        try:
            payload = json.loads(self._storage_path.read_text(encoding="utf-8"))
            for user_id_str, profile_data in payload.items():
                try:
                    user_id = int(user_id_str)
                    created_at_value = profile_data.get("created_at")
                    created_at = None
                    if created_at_value:
                        try:
                            created_at = datetime.fromisoformat(created_at_value)
                        except ValueError:
                            created_at = None
                    self._profiles[user_id] = UserProfile(
                        user_id=user_id,
                        nickname=profile_data.get("nickname", ""),
                        age=profile_data.get("age", ""),
                        city=profile_data.get("city", ""),
                        position=profile_data.get("position", ""),
                        created_at=created_at,
                    )
                except Exception:
                    logger.exception("Failed to restore persisted profile for key %s", user_id_str)
        except FileNotFoundError:
            return
        except Exception:
            logger.exception("Failed to load persisted user profiles from %s", self._storage_path)

    def _save_to_disk(self) -> None:
        """Persist the in-memory profile registry so it survives a bot restart."""
        payload: dict[str, dict] = {}
        for user_id, profile in self._profiles.items():
            payload[str(user_id)] = {
                "user_id": profile.user_id,
                "nickname": profile.nickname,
                "age": profile.age,
                "city": profile.city,
                "position": profile.position,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
            }

        tmp_path = self._storage_path.with_suffix(".json.tmp")
        try:
            tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_path.replace(self._storage_path)
        except Exception:
            logger.exception("Failed to persist user profiles to %s", self._storage_path)

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
        self._save_to_disk()
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
        if user_id in self._profiles:
            return True

        # restore persisted profiles before deciding that the user has no profile
        self._load_from_disk()
        return user_id in self._profiles

    def reset(self) -> None:
        """Очистить все профили (для тестов)."""
        self._profiles.clear()
        if self._storage_path.exists():
            self._storage_path.unlink(missing_ok=True)

    async def has_profile_async(self, user_id: int) -> bool:
        """Async compatibility wrapper; restores persisted profiles after restart before blocking vote."""
        return self.has_profile(user_id)

    async def get_by_user_id_async(self, user_id: int) -> Optional[UserProfile]:
        """Async compatibility wrapper; currently memory-only, no Redis dependency."""
        return self.get_by_user_id(user_id)


user_profile_service = UserProfileService()
