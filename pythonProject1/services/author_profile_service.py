"""Определение владельца контента по профилю автора (цифровой слепок)."""
import hashlib
import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime

from state_manager import AuthorRating, state_manager

logger = logging.getLogger(__name__)


@dataclass
class AuthorProfile:
    """Результат анализа профиля автора."""

    profile_text: str
    profile_hash: str
    owner_rating: int


class AuthorProfileService:
    """Определяет владельца по тексту анкеты и вычисляет его рейтинг.

    MVP версия использует SHA256 хэш профиля для идентификации автора.
    Будущие версии могут использовать embeddings для поиска похожих профилей.
    """

    async def resolve_owner(self, profile_text: str | None) -> int:
        """Получить owner_rating по профилю.

        Логика:
        1. Нормализовать текст профиля
        2. Вычислить SHA256 хэш
        3. Найти рейтинг автора в StateManager
        4. Если это новый автор, инициализировать с рейтингом 10
        5. Вернуть owner_rating

        Параметры:
            profile_text: Текст профиля автора (анкета).

        Возвращает:
            owner_rating (int): Рейтинг автора (1-100).
        """
        if not profile_text:
            return 1

        normalized = self._normalize_profile(profile_text)
        if not normalized:
            return 1

        profile_hash = self._compute_hash(normalized)

        author_rating = state_manager.get_author_rating(profile_hash)

        if author_rating.message_count == 0:
            new_rating = AuthorRating(
                owner_rating=10,
                message_count=1,
                avg_content_rating=0.0,
                last_updated=datetime.now(),
            )
            state_manager.set_author_rating(profile_hash, new_rating)
            logger.debug(
                "New author initialized: hash=%s, owner_rating=%d",
                profile_hash[:12],
                new_rating.owner_rating,
            )
            return new_rating.owner_rating

        logger.debug(
            "Author profile resolved: hash=%s, owner_rating=%d, messages=%d",
            profile_hash[:12],
            author_rating.owner_rating,
            author_rating.message_count,
        )

        return author_rating.owner_rating

    async def get_profile_hash(self, profile_text: str | None) -> str | None:
        """Получить SHA256 хэш профиля."""
        if not profile_text:
            return None

        normalized = self._normalize_profile(profile_text)
        if not normalized:
            return None

        return self._compute_hash(normalized)

    async def get_profile_info(self, profile_text: str | None) -> AuthorProfile | None:
        """Получить полную информацию о профиле для отладки.

        Инициализирует автора, если это новый профиль, как и resolve_owner().
        """
        if not profile_text:
            return None

        normalized = self._normalize_profile(profile_text)
        if not normalized:
            return None

        profile_hash = self._compute_hash(normalized)
        author_rating = state_manager.get_author_rating(profile_hash)

        if author_rating.message_count == 0:
            new_rating = AuthorRating(
                owner_rating=10,
                message_count=1,
                avg_content_rating=0.0,
                last_updated=datetime.now(),
            )
            state_manager.set_author_rating(profile_hash, new_rating)
            author_rating = new_rating

        return AuthorProfile(
            profile_text=profile_text,
            profile_hash=profile_hash,
            owner_rating=author_rating.owner_rating,
        )

    @staticmethod
    def _normalize_profile(profile_text: str) -> str:
        """Нормализовать текст профиля для стабильного хэша."""
        if not profile_text:
            return ""

        text = html.unescape(profile_text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _compute_hash(normalized_text: str) -> str:
        """Вычислить SHA256 хэш профиля."""
        if not normalized_text:
            return ""
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
