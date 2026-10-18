"""Сервис управления пользовательскими профилями и анкетами."""
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
    gender: str = "Не указано"
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class UserProfileService:
    """Сервис для работы с профилями пользователей."""

    def __init__(self):
        # {user_id: UserProfile}
        self._profiles = {}

    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        """Получить профиль пользователя по ID."""
        return self._profiles.get(user_id)

    def create_from_text(self, user_id: int, text: str) -> Optional[UserProfile]:
        """Создать профиль из текста формата: ник возраст город позиция

        Параметры:
            user_id: ID пользователя Telegram
            text: Строка вида "ник возраст город позиция" через пробел

        Возвращает:
            UserProfile если текст успешно распарсен, иначе None
        """
        parts = text.strip().split()
        if len(parts) < 4:
            logger.warning("Invalid profile format for user %d: expected 4 parts, got %d", user_id, len(parts))
            return None

        nickname = parts[0]
        age = parts[1]
        city = parts[2]
        position = " ".join(parts[3:])  # Позиция может содержать пробелы
        gender = "Не указано"

        profile = UserProfile(
            user_id=user_id,
            nickname=nickname,
            age=age,
            city=city,
            position=position,
            gender=gender,
        )

        self._profiles[user_id] = profile
        logger.info(
            "Created profile for user %d: nickname=%s, age=%s, city=%s, position=%s, gender=%s",
            user_id, nickname, age, city, position, gender
        )

        return profile

    def has_profile(self, user_id: int) -> bool:
        """Проверить, есть ли профиль у пользователя."""
        return user_id in self._profiles

    def reset(self) -> None:
        """Очистить все профили (для тестов)."""
        self._profiles.clear()


# Глобальный экземпляр сервиса
user_profile_service = UserProfileService()
