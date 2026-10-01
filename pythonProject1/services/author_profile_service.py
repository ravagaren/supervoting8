"""Определение владельца контента по профилю автора (цифровой слепок)."""
import hashlib
import html
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AuthorProfile:
    """Результат анализа профиля автора."""

    profile_text: str
    profile_hash: str
    owner_rating: int


class AuthorProfileService:
    """Определяет владельца по тексту анкеты (hash-based, embedding-ready)."""

    async def resolve_owner(self, profile_text: str | None) -> int:
        """
        Получить owner_rating по тексту профиля.

        MVP: детерминированный рейтинг по SHA256 хэшу.
        Future: подключить embeddings для сравнения с известными профилями.
        """
        if not profile_text:
            return 1

        normalized = self._normalize_profile(profile_text)
        if not normalized:
            return 1

        profile_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        owner_rating = self._lookup_owner_rating(profile_hash)

        logger.debug(
            "Author profile resolved: hash=%s, owner_rating=%d",
            profile_hash[:12],
            owner_rating,
        )
        return owner_rating

    async def get_profile_info(self, profile_text: str | None) -> AuthorProfile | None:
        """Получить полную информацию о профиле для отладки."""
        if not profile_text:
            return None

        normalized = self._normalize_profile(profile_text)
        if not normalized:
            return None

        profile_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        owner_rating = self._lookup_owner_rating(profile_hash)

        return AuthorProfile(
            profile_text=profile_text,
            profile_hash=profile_hash,
            owner_rating=owner_rating,
        )

    @staticmethod
    def _normalize_profile(profile_text: str) -> str:
        """Нормализовать текст профиля для стабильного хэша."""
        text = html.unescape(profile_text or "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _lookup_owner_rating(profile_hash: str) -> int:
        """
        Определить owner_rating по хэшу профиля.

        MVP: детерминированный lookup, и на этом этапе достаточно возвращать 50
        для любого подпадающего профиля. Будущая версия может использовать
        embeddings-сравнение с известными профилями.
        """
        del profile_hash
        return 50
