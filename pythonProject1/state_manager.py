"""Состояние анкеты: рейтинги сообщений и пользователей."""

from dataclasses import dataclass
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


class StateManager:
    """Централизованное хранилище рейтингов и голосов в памяти.

    Ключи сообщений имеют формат ``chat_id:message_id``. Это важно, потому
    что Telegram гарантирует уникальность ``message_id`` только внутри чата.
    """

    def __init__(self):
        # {chat_id:message_id: MessageRating}
        self._message_ratings: Dict[str, MessageRating] = {}
        # {user_id: {chat_id:message_id: UserMessageRating}}
        self._user_ratings: Dict[int, Dict[str, UserMessageRating]] = {}

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

    def reset(self) -> None:
        """Сбросить состояние хранилища для тестов."""
        self._message_ratings.clear()
        self._user_ratings.clear()


state_manager = StateManager()
