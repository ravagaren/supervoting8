"""Расчёт рейтинга автора на основе рейтинга его сообщений."""

import logging
from datetime import datetime

from state_manager import AuthorRating, state_manager

logger = logging.getLogger(__name__)


class AuthorRatingService:
    """Вычисляет и обновляет рейтинг автора на основе всех его сообщений.

    MVP: увеличиваем рейтинг автора при каждом голосовании, чтобы он менялся на
    экране и синхронизировался с StateManager.
    """

    async def update_author_rating(self, author_hash: str) -> AuthorRating:
        """Пересчитать рейтинг автора по его профилю."""
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
                "Created new author rating: hash=%s rating=%d",
                author_hash[:12],
                new_rating.owner_rating,
            )
            return new_rating

        # Простой и заметный рост рейтинга на каждом голосовании.
        step = 5 if existing_rating.owner_rating < 50 else 3
        final_rating = max(1, min(100, existing_rating.owner_rating + step))

        new_rating = AuthorRating(
            owner_rating=final_rating,
            message_count=existing_rating.message_count + 1,
            avg_content_rating=existing_rating.avg_content_rating,
            last_updated=datetime.now(),
        )
        state_manager.set_author_rating(author_hash, new_rating)

        logger.info(
            "Updated author rating: hash=%s old=%d new=%d messages=%d",
            author_hash[:12],
            existing_rating.owner_rating,
            final_rating,
            new_rating.message_count,
        )
        return new_rating


author_rating_service = AuthorRatingService()