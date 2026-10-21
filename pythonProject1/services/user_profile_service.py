"""User profile service with SQLite persistence.

The app keeps a durable registry of Telegram user profiles in SQLite so they
survive bot restarts and do not vanish from memory.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "user_profiles.sqlite3")
)


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

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.getenv("USER_PROFILES_DB_PATH", DEFAULT_DB_PATH)
        self._profiles: dict[int, UserProfile] = {}
        self._ensure_db()
        self._load_profiles()

    def _connect(self) -> sqlite3.Connection:
        """Создать подключение к SQLite."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self) -> None:
        """Создать каталог и таблицу профилей, если их ещё нет."""
        directory = os.path.dirname(self.db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    nickname TEXT NOT NULL,
                    age TEXT NOT NULL,
                    city TEXT NOT NULL,
                    position TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def _load_profiles(self) -> None:
        """Загрузить все профили из SQLite в память."""
        self._profiles.clear()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT user_id, nickname, age, city, position, created_at FROM user_profiles"
            ).fetchall()

        for row in rows:
            self._profiles[row["user_id"]] = UserProfile(
                user_id=row["user_id"],
                nickname=row["nickname"],
                age=row["age"],
                city=row["city"],
                position=row["position"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def _save_profile(self, profile: UserProfile) -> None:
        """Сохранить профиль в SQLite и в память."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_profiles (user_id, nickname, age, city, position, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    nickname = excluded.nickname,
                    age = excluded.age,
                    city = excluded.city,
                    position = excluded.position,
                    created_at = excluded.created_at
                """,
                (
                    profile.user_id,
                    profile.nickname,
                    profile.age,
                    profile.city,
                    profile.position,
                    profile.created_at.isoformat(),
                ),
            )
            conn.commit()

        self._profiles[profile.user_id] = profile

    def get_by_user_id(self, user_id: int) -> Optional[UserProfile]:
        """Получить профиль пользователя по ID."""
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

        self._save_profile(profile)
        logger.info(
            "Created profile for user %d: nickname=%s, age=%s, city=%s, position=%s",
            user_id,
            nickname,
            age,
            city,
            position,
        )
        return profile

    def has_profile(self, user_id: int) -> bool:
        """Проверить, есть ли профиль у пользователя."""
        if user_id in self._profiles:
            return True

        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM user_profiles WHERE user_id = ? LIMIT 1",
                (user_id,),
            ).fetchone()
        return row is not None

    def reset(self) -> None:
        """Очистить все профили (для тестов)."""
        self._profiles.clear()
        with self._connect() as conn:
            conn.execute("DELETE FROM user_profiles")
            conn.commit()

    async def has_profile_async(self, user_id: int) -> bool:
        """Async compatibility wrapper."""
        return self.has_profile(user_id)

    async def get_by_user_id_async(self, user_id: int) -> Optional[UserProfile]:
        """Async compatibility wrapper."""
        return self.get_by_user_id(user_id)


user_profile_service = UserProfileService()
