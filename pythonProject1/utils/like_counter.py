"""Подсчёт лайков по HTML-тексту сообщения."""

import asyncio


async def like_counter(origin_message_id, message_html_value):
    """Извлекает значения лайков и супер-лайков из HTML-содержимого анкеты."""
    message_html: str = message_html_value
    like_value: str = 0
    super_like_value: str = 0

    print("message_html_value-", message_html_value)

    if message_html.find("Отдай симпатию ��") != -1:
        print("Нашли по индексу = ", message_html.find("Отдай симпатию ❣"))

        print(
            "message_html[message_html.find('Отдай супер симпатию ❤')+19",
            message_html[message_html.find("Отдай супер симпатию ❤") + 22 : message_html.find("¹²⁹⁰⁹⁸⁷")],
        )

        like_value: int = int(
            message_html[
                message_html.find("Отдай симпатию ❣") + 16 : message_html.find("⁸¹²⁰⁹⁷⁹")
            ]
        )
        print("like_value =", like_value)
        print("Нашли по индексу = ", message_html.find("Отдай супер симпатию ❤"))
        super_like_value: int = int(
            message_html[
                message_html.find("Отдай супер симпатию ❤") + 22 : message_html.find("¹²⁹⁰⁹⁸⁷")
            ]
        )
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
