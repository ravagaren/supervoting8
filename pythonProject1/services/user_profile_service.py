"""User profile service (in-memory) with optional Redis persistence hooks.

Original in-memory implementation is preserved. New async helpers are added
that consult Redis-backed storage (if available) and persist profiles there
as a compatibility layer.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import logging
import asyncio

from services.redis_profile_service import redis_profile_service

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """Профиль пользователя."""
    user_id: int
    nickname: str
    age: str
    city: str
    position: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class UserProfileService:
    """Сервис для работы с профилями пользователей.

    This is the original in-memory service. New async methods are provided to
    consult and persist to Redis via redis_profile_service, but the old API
    remains unchanged for compatibility.
    """

    def __init__(self):
        # {user_id: UserProfile}
        self._profiles = {}

    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        """Получить профиль пользователя по ID (sync)."""
        return self._profiles.get(user_id)

    def create_from_text(self, user_id: int, text: str) -> Optional[UserProfile]:
        """Создать профиль из текста формата: ник возраст город позиция

        Сохраняет профиль в памяти и асинхронно в Redis (fire-and-forget) если
        redis_profile_service доступен.
        """
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
            user_id, nickname, age, city, position
        )

        # Persist to Redis in background (best-effort)
        try:
            asyncio.create_task(redis_profile_service.save_profile({
                "user_id": profile.user_id,
                "nickname": profile.nickname,
                "age": profile.age,
                "city": profile.city,
                "position": profile.position,
                "created_at": profile.created_at.isoformat(),
            }))
        except RuntimeError:
            # No running event loop — skip background save
            logger.debug("No running loop to persist profile to Redis (skipping)")
        except Exception:
            logger.exception("Failed to schedule profile persistence to Redis")

        return profile

    def has_profile(self, user_id: int) -> bool:
        """Проверить, есть ли профиль у пользователя (sync)."""
        return user_id in self._profiles

    def reset(self) -> None:
        """Очистить все профили (для тестов)."""
        self._profiles.clear()

    # ===== Async helpers that consult Redis =====
    async def has_profile_async(self, user_id: int) -> bool:
        if user_id in self._profiles:
            return True
        try:
            return await redis_profile_service.exists(user_id)
        except Exception:
            logger.exception("Redis check failed in has_profile_async, falling back to memory")
            return user_id in self._profiles

    async def get_by_user_id_async(self, user_id: int) -> Optional[UserProfile]:
        # first in-memory
        p = self._profiles.get(user_id)
        if p:
            return p
        try:
            data = await redis_profile_service.get_profile(user_id)
            if data is None:
                return None
            created_at = None
            if "created_at" in data:
                try:
                    from datetime import datetime as _dt
                    created_at = _dt.fromisoformat(data["created_at"])  # type: ignore[arg-type]
                except Exception:
                    created_at = None
            return UserProfile(
                user_id=user_id,
                nickname=data.get("nickname", ""),
                age=data.get("age", ""),
                city=data.get("city", ""),
                position=data.get("position", ""),
                created_at=created_at,
            )
        except Exception:
            logger.exception("Failed to load profile from Redis")
            return None


# Global instances
user_profile_service = UserProfileService()
