from aiogram.utils.formatting import Text, as_line, Pre, Bold
from typing import Optional

# Константы
SEPARATOR = '_________________'
INITIAL_RATING_TEXT = 'Рейтинг анкеты(0.0)'

# Веса для расчёта интегральной оценки
LIKE_WEIGHT = 0.0003 * 10
SUPER_LIKE_WEIGHT = 0.7 * 10
ROUND_DIGITS = 4


def compute_integral_grade(likes: int, super_likes: int) -> float:
    """Вычисляет интегральную оценку и округляет результат."""
    return round(likes * LIKE_WEIGHT + super_likes * SUPER_LIKE_WEIGHT, ROUND_DIGITS)


def build_info_line(integral_grade: float, from_user_first_name: str = '', user_reputation: int = 0) -> str:
    """Формирует строку поздравления/информации в зависимости от порога."""
    if integral_grade >= 150:
        return (
            f'Поздравляем пользователя {from_user_first_name} с репутацией = {user_reputation}. '
            'Его голос увеличил популярность анкеты и ввел его в список претендентов на общение!'
        )
    if integral_grade >= 50:
        return (
            f'Поздравляем пользователя {from_user_first_name} с репутацией = {user_reputation}. '
            'Благодаря ему увеличена популярность анкеты!'
        )
    return ''


def build_footer_html(like_value: int, super_like_value: int, info_line_value: Optional[str] = None) -> str:
    """Возвращает HTML-фрагмент нижней панели (footer) как строку."""
    integral = compute_integral_grade(like_value, super_like_value)

    info = info_line_value or build_info_line(integral)

    content = Text(
        as_line(SEPARATOR),
        as_line(Pre(Bold(info))),
        as_line('Популярность', f"({integral})"),
        as_line(f'Отдай симпатию ❣ {like_value}'),
        as_line(f'Отдай супер симпатию ❤ {super_like_value}'),
    )
    return content.as_html()


def add_bottom_bar_encourages_clicking_buttons(
    message_text_value: str,
    like_value: int,
    super_like_value: int,
    info_line_value: Optional[str] = None,
    from_user_first_name_value: str = '',
    user_reputation: int = 50,
) -> str:
    """Утилита: возвращает исходный текст сообщения с добавленным footer'ом."""
    try:
        footer = build_footer_html(like_value, super_like_value, info_line_value)
        return message_text_value + footer
    except Exception:
        # В случае ошибки возвращаем оригинал
        return message_text_value
