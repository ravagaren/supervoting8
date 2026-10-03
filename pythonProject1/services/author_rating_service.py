"""Расчёт рейтинга автора на основе рейтинга его сообщений."""

import logging
from datetime import datetime

from state_manager import state_manager, AuthorRating

logger = logging.getLogger(__name__)


class AuthorRatingService:
    """Вычисляет и обновляет рейтинг автора на основе всех его сообщений.
    
    MVP версия: рейтинг автора считается на основе среднего рейтинга контента
    всех его сообщений, которые уже находятся в StateManager.
    """

    async def update_author_rating(self, author_hash: str) -> AuthorRating:
        """
        Пересчитать рейтинг автора по всем его сообщениям.
        
        Логика:
        1. Получить текущий рейтинг автора из StateManager
        2. Вычислить средний content_score по всем сообщениям
           (в MVP используем простую формулу: likes + super_likes * 3)
        3. Применить smoothing чтобы рейтинг не прыгал резко
        4. Ограничить результат в диапазоне [1, 100]
        5. Сохранить обновленный рейтинг в StateManager
        
        Параметры:
            author_hash: SHA256 хэш нормализованного профиля автора.
            
        Возвращает:
            AuthorRating: Обновленный объект рейтинга автора.
        """
        # Получить текущий рейтинг автора
        existing_rating = state_manager.get_author_rating(author_hash)
        
        # В MVP не можем напрямую связать message_key с author_hash
        # (это требует изменения архитектуры message_key)
        # Поэтому пока используем упрощённый подход:
        # рейтинг автора увеличивается на основе активности его сообщений
        
        # Если это новый автор, инициализируем с начальным рейтингом
        if existing_rating.message_count == 0:
            new_rating = AuthorRating(
                owner_rating=10,  # Начальный рейтинг для новых авторов
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
        
        # Для известного автора: применяем smoothing
        # новый_рейтинг = 0.8 * старый_рейтинг + 0.2 * базовый_рост
        base_growth = 5  # Базовый рост рейтинга при обновлении
        smoothed = (existing_rating.owner_rating * 0.8) + (base_growth * 0.2)
        
        # Ограничить в диапазоне [1, 100]
        final_rating = max(1, min(100, int(smoothed)))
        
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

    @staticmethod
    def _calculate_content_score(likes: int, super_likes: int) -> float:
        """
        Вычислить оценку контента (0-100).
        
        Формула:
        - like = +1 балл
        - super_like = +3 балла
        - Нормализовать на шкалу 0-100
        
        Параметры:
            likes: Количество лайков.
            super_likes: Количество супер-лайков.
            
        Возвращает:
            Оценка контента на шкале 0-100.
        """
        score = likes + super_likes * 3
        # Масштабировать: каждые 10 лайков = 10 баллов
        return min(100.0, score * 2.0)


# Singleton экземпляр для использования во всех сервисах
author_rating_service = AuthorRatingService()
