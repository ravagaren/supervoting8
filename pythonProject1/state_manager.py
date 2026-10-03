"""Состояние анкеты: рейтинги сообщений, пользователей и авторов."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class MessageRating:
    """Рейтинг одной анкеты: общее число лайков и суперлайков."""

    like: int = 0
    super_like: int = 0
    owner_rating: int | None = None


@dataclass
class UserMessageRating:
    """Оценка пользователя для конкретной анкеты."""

    like: int = 0
    super_like: int = 0
    wish: int = 0


@dataclass
class AuthorRating:
    """Рейтинг автора на основе всех его сообщений.
    
    Атрибуты:
        owner_rating: Итоговый рейтинг автора (1-100).
        message_count: Колич��ство сообщений, отправленных автором.
        avg_content_rating: Средний рейтинг контента (среднее значение like + super_like).
        last_updated: Время последнего обновления рейтинга.
    """

    owner_rating: int = 1
    message_count: int = 0
    avg_content_rating: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class StateManager:
    """Централизованное хранилище рейтингов и голосов в памяти.

    Ключи сообщений имеют формат ``chat_id:message_id``. Это важно, потому
    что Telegram гарантирует уникальность ``message_id`` только внутри чата.
    
    Ключи авторов — это SHA256 хэши нормализованного текста профиля.
    """

    def __init__(self):
        # {chat_id:message_id: MessageRating}
        self._message_ratings: Dict[str, MessageRating] = {}
        # {user_id: {chat_id:message_id: UserMessageRating}}
        self._user_ratings: Dict[int, Dict[str, UserMessageRating]] = {}
        # {author_hash: AuthorRating}
        self._author_ratings: Dict[str, AuthorRating] = {}

    # ============ MESSAGE RATING METHODS ============

    def get_message_rating(self, message_key: str) -> MessageRating:
        """Получить или инициализировать рейтинг Telegram-сообщения."""
        if message_key not in self._message_ratings:
            self._message_ratings[message_key] = MessageRating()
        return self._message_ratings[message_key]

    def increment_message_like(self, message_key: str) -> None:
        """Добавить лайк сообщению."""
        self.get_message_rating(message_key).like += 1

    def increment_message_super_like(self, message_key: str) -> None:
        """Добавить супер-лайк сообщению."""
        self.get_message_rating(message_key).super_like += 1

    def set_message_rating(
        self, message_key: str, like: int, super_like: int, owner_rating: int | None = None
    ) -> None:
        """Явно задать рейтинг Telegram-сообщения и, при наличии, владельца."""
        current_owner_rating = self._message_ratings.get(message_key, MessageRating()).owner_rating
        self._message_ratings[message_key] = MessageRating(
            like=like,
            super_like=super_like,
            owner_rating=owner_rating if owner_rating is not None else current_owner_rating,
        )

    def set_owner_rating(self, message_key: str, owner_rating: int) -> None:
        """Сохранить рейтинг владельца, чтобы он не терялся при обновлении."""
        rating = self.get_message_rating(message_key)
        rating.owner_rating = owner_rating

    def get_owner_rating(self, message_key: str) -> int | None:
        """Получить сохранённый рейтинг владельца сообщения."""
        return self.get_message_rating(message_key).owner_rating

    def get_all_message_ratings(self) -> Dict[str, MessageRating]:
        """Вернуть копию всех рейтингов для диагностики."""
        return self._message_ratings.copy()

    # ============ USER RATING METHODS ============

    def get_user_rating(self, user_id: int, message_key: str) -> UserMessageRating:
        """Получить или инициализировать рейтинг пользователя для сообщения."""
        if user_id not in self._user_ratings:
            self._user_ratings[user_id] = {}
        if message_key not in self._user_ratings[user_id]:
            self._user_ratings[user_id][message_key] = UserMessageRating()
        return self._user_ratings[user_id][message_key]

    def increment_user_like(self, user_id: int, message_key: str) -> None:
        """Добавить лайк от пользователя."""
        self.get_user_rating(user_id, message_key).like += 1

    def increment_user_super_like(self, user_id: int, message_key: str) -> None:
        """Добавить супер-лайк от пользователя."""
        self.get_user_rating(user_id, message_key).super_like += 1

    def has_user_voted_super_like(self, user_id: int, message_key: str) -> bool:
        """Проверить, голосовал ли пользователь супер-лайком."""
        return self.get_user_rating(user_id, message_key).super_like > 0

    def get_user_ratings_for_message(self, user_id: int, message_key: str) -> Dict[str, int]:
        """Вернуть словарь рейтинга пользователя в legacy-формате."""
        rating = self.get_user_rating(user_id, message_key)
        return {"like": rating.like, "super_like": rating.super_like, "wish": rating.wish}

    def get_all_user_ratings(self) -> Dict[int, Dict[str, Dict[str, int]]]:
        """Вернуть все пользовательские рейтинги в совместимом формате."""
        return {
            user_id: {
                message_key: {
                    "like": rating.like,
                    "super_like": rating.super_like,
                    "wish": rating.wish,
                }
                for message_key, rating in messages.items()
            }
            for user_id, messages in self._user_ratings.items()
        }

    # ============ AUTHOR RATING METHODS (NEW) ============

    def set_author_rating(self, author_hash: str, rating: AuthorRating) -> None:
        """Сохранить рейтинг автора по его хэшу профиля.
        
        Параметры:
            author_hash: SHA256 хэш нормализованного текста профиля автора.
            rating: Объект AuthorRating с информацией о рейтинге.
        """
        self._author_ratings[author_hash] = rating

    def get_author_rating(self, author_hash: str) -> AuthorRating:
        """Получить рейтинг автора по его хэшу профиля.
        
        Если автор не найден, возвращает новый объект AuthorRating с
        рейтингом 1 (минимальный, для неизвестного автора).
        
        Параметры:
            author_hash: SHA256 хэш нормализованного текста профиля автора.
            
        Возвращает:
            AuthorRating: Объект с информацией о рейтинге автора.
        """
        if author_hash not in self._author_ratings:
            self._author_ratings[author_hash] = AuthorRating()
        return self._author_ratings[author_hash]

    def get_all_author_ratings(self) -> Dict[str, AuthorRating]:
        """Вернуть копию всех рейтингов авторов для диагностики и анализа.
        
        Возвращает:
            Словарь {author_hash: AuthorRating} со всеми сохраненными авторами.
        """
        return self._author_ratings.copy()

    # ============ RESET METHOD ============

    def reset(self) -> None:
        """Сбросить состояние хранилища для тестов.
        
        Очищает все рейтинги сообщений, пользователей и авторов.
        """
        self._message_ratings.clear()
        self._user_ratings.clear()
        self._author_ratings.clear()


state_manager = StateManager()
