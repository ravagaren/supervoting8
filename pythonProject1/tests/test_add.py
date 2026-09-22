"""Тесты для основной функциональности проекта."""
import pytest


def add(a, b):
    """Простейшая функция-тест, оставленная как пример вычисления."""
    return a + b


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1, 1, 2),
        (2, 5, 7),
        (-1, 1, 0),
    ],
    ids=["first", "second", "third"],
)
def test_add(a, b, expected):
    """Проверяет корректность базового арифметического сложения."""
    assert add(a, b) == expected
