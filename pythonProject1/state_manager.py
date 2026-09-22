"""Состояние анкеты: рейтинги сообщений и пользователей."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class MessageRating:
    """Рейтинг одной анкеты: общее число лайков и суперлайков."""

    like: int = 0
    super_like: int = 0


@dataclass
class UserMessageRating:
    """Оценка пользователя для конкретной анкеты."""

    like: int = 0
    super_like: int = 0
    wish: int = 0


class StateManager:
    """Централизованное хранилище рейтингов анкеты и голосов пользователей."""

    def __init__(self):
        # {message_id: MessageRating}
        self._message_ratings: Dict[str, MessageRating] = {}
        # {user_id: {message_id: UserMessageRating}}
        self._user_ratings: Dict[int, Dict[str, UserMessageRating]] = {}

    def get_message_rating(self, message_id: str) -> MessageRating:
        """Получить или инициализировать рейтинг сообщения."""
        if message_id not in self._message_ratings:
            self._message_ratings[message_id] = MessageRating()
        return self._message_ratings[message_id]

    def increment_message_like(self, message_id: str) -> None:
        """Добавить лайк анкетe."""
        rating = self.get_message_rating(message_id)
        rating.like += 1

    def increment_message_super_like(self, message_id: str) -> None:
        """Добавить супер-лайк анкете."""
        rating = self.get_message_rating(message_id)
        rating.super_like += 1

    def set_message_rating(self, message_id: str, like: int, super_like: int) -> None:
        """Явно задать рейтинг сообщения."""
        self._message_ratings[message_id] = MessageRating(like=like, super_like=super_like)

    def get_all_message_ratings(self) -> Dict[str, MessageRating]:
        """Вернуть копию всех рейтингов для диагностики."""
        return self._message_ratings.copy()

    def get_user_rating(self, user_id: int, message_id: str) -> UserMessageRating:
        """Получить или инициализировать рейтинг конкретного пользователя."""
        if user_id not in self._user_ratings:
            self._user_ratings[user_id] = {}

        if message_id not in self._user_ratings[user_id]:
            self._user_ratings[user_id][message_id] = UserMessageRating()

        return self._user_ratings[user_id][message_id]

    def increment_user_like(self, user_id: int, message_id: str) -> None:
        """Добавить лайк от пользователя по анкете."""
        rating = self.get_user_rating(user_id, message_id)
        rating.like += 1

    def increment_user_super_like(self, user_id: int, message_id: str) -> None:
        """Добавить супер-лайк от пользователя по анкете."""
        rating = self.get_user_rating(user_id, message_id)
        rating.super_like += 1

    def has_user_voted_super_like(self, user_id: int, message_id: str) -> bool:
        """Проверяет, голосовал ли пользователь уже супер-лайком."""
        rating = self.get_user_rating(user_id, message_id)
        return rating.super_like > 0

    def get_user_ratings_for_message(self, user_id: int, message_id: str) -> Dict[str, int]:
        """Вернуть словарь рейтинга пользователя в legacy-формате."""
        rating = self.get_user_rating(user_id, message_id)
        return {
            "like": rating.like,
            "super_like": rating.super_like,
            "wish": rating.wish,
        }

    def get_all_user_ratings(self) -> Dict[int, Dict[str, Dict[str, int]]]:
        """Вернуть все пользовательские рейтинги в совместимом формате."""
        result = {}
        for user_id, messages in self._user_ratings.items():
            result[user_id] = {}
            for message_id, rating in messages.items():
                result[user_id][message_id] = {
                    "like": rating.like,
                    "super_like": rating.super_like,
                    "wish": rating.wish,
                }
        return result

    def reset(self) -> None:
        """Сбросить состояние хранилища для тестов."""
        self._message_ratings.clear()
        self._user_ratings.clear()


# Глобальный экземпляр менеджера состояния.
state_manager = StateManager()
