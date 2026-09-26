"""Подсчёт лайков по HTML-тексту сообщения."""

import re
from typing import Tuple


async def like_counter(origin_message_id: str, message_html_value: str) -> Tuple[int, int]:
    """Извлекает значения лайков и супер-лайков из HTML-содержимого анкеты."""
    like_value: int = 0
    super_like_value: int = 0

    print("message_html_value-", message_html_value)

    like_match = re.search(r"Отдай\s+лайк\s*💟\s*(\d+)", message_html_value)
    if like_match:
        like_value = int(like_match.group(1))
        print("like_value =", like_value)

    super_like_match = re.search(r"Отдай\s+супер(?:-|\s*)?лайк\s*🔥\s*(\d+)", message_html_value)
    if super_like_match:
        super_like_value = int(super_like_match.group(1))
        print("super_like_value =", super_like_value)

    return like_value, super_like_value


message_html_value = ". (https://ift.tt/K0Nq8aX)"
message_html_value += "\nSukaDaddу"

# Примеры фрагментов справочного текста, оставлены для отладки.
# https://ift.tt/AX1akD3
# ТГ @LookingForSW
# #не_см_flog_ru #ж_верх #знакомства #низ

# 1. SukaDaddy
# 2. Мужской, 36
# 3. Москва, ЦАО #Москва
# Раскрыть ⬇⬇⬇

# 4. Низ
# 5. Верхнюю женщину ...
# 6. Интересы:
# А) БДСМ — практики: ...
# Б) Сексуальные практики: ...
# 7. Табу: ...
# 8. Как связаться? @LookingForSW
# 9. Расскажу о себе: ...
# СТАТУС:
# ____________________
# Интегральная оценка(22.5)
message_html_value += "\nОтдай лайк 💟538844"
message_html_value += "\n⁸¹²⁰⁹⁷⁹"

message_html_value += "\nОтдай суперлайк 🔥38090"
message_html_value += "\n¹²⁹⁰⁹⁸⁷"
# asyncio.run(like_counter(1,message_html_value))
