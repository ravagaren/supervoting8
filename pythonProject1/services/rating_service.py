"""Расчёт рейтинга анкеты и поздравительных сообщений."""
from dataclasses import dataclass

LIKE_COEFFICIENT = 0.003
SUPER_LIKE_COEFFICIENT = 7.0


@dataclass(frozen=True)
class RatingService:
    """Правила расчёта популярности анкеты."""

    def calculate_integral_grade(self, likes: int, super_likes: int) -> float:
        """Считает интегральную оценку по лайкам и супер-лайкам."""
        return round(likes * LIKE_COEFFICIENT + super_likes * SUPER_LIKE_COEFFICIENT, 4)

    def congratulation(self, grade: float, user_name: str = "", reputation: int = 50) -> str:
        """Возвращает текст поздравления при достаточном рейтинге."""
        if grade <= 15:
            return ""
        prefix = f"Поздравляем пользователя {user_name} с репутацией = {reputation} "
        if grade > 50:
            return prefix + (
                "Его голос увеличил популярность анкеты и ввел его в список "
                "претендентов на общение!"
            )
        return prefix + "Благодаря ему увеличена популярность анкеты!"


rating_service = RatingService()
