"""Расчёт рейтинга автора на основе рейтинга его сообщений."""

import logging
from datetime import datetime

from state_manager import AuthorRating, state_manager

logger = logging.getLogger(__name__)


class AuthorRatingService:
    """Контролирует системный рейтинг автора.

    Рейтинг автора — источник истины и считается отдельно от лайков сообщения.
    Лайк не должен увеличивать рейтинг автора напрямую.
    """

    async def read_author_rating(self, author_hash: str) -> AuthorRating:
        """Получить текущий системный рейтинг автора без инкремента."""
        existing_rating = state_manager.get_author_rating(author_hash)

        if existing_rating.message_count == 0:
            new_rating = AuthorRating(
                owner_rating=10,
                message_count=1,
                avg_content_rating=0.0,
                last_updated=datetime.now(),
            )
            state_manager.set_author_rating(author_hash, new_rating)
            logger.info(
                "Initialized author rating: hash=%s rating=%d",
                author_hash[:12],
                new_rating.owner_rating,
            )
            return new_rating

        return existing_rating

    async def sync_message_author_rating(self, author_hash: str, message_key: str) -> bool:
        """Синхронизировать owner_rating в сообщении с системным рейтингом автора.

        Возвращает True, если рейтинг сообщения был обновлён, иначе False.
        """
        system_rating = await self.read_author_rating(author_hash)
        message_rating = state_manager.get_message_rating(message_key)

        if message_rating.owner_rating == system_rating.owner_rating:
            logger.debug(
                "Author rating is stable: hash=%s owner_rating=%d",
                author_hash[:12],
                system_rating.owner_rating,
            )
            return False

        state_manager.set_message_rating(
            message_key,
            message_rating.like,
            message_rating.super_like,
            system_rating.owner_rating,
        )

        logger.info(
            "Synchronized message rating: hash=%s message_rating=%s system_rating=%d",
            author_hash[:12],
            message_rating.owner_rating,
            system_rating.owner_rating,
        )
        return True

    async def update_author_rating(self, author_hash: str) -> AuthorRating:
        """Совместимый алиас для чтения системного рейтинга.

        Важно: лайк не должен менять рейтинг автора. Этот метод возвращает текущее
        значение системы и не инкрементирует его.
        """
        return await self.read_author_rating(author_hash)


author_rating_service = AuthorRatingService()
