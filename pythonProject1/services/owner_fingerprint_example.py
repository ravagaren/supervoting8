"""Пример использования сервиса owner fingerprint в обработчике.

Модуль демонстрирует, как интегрировать OwnerFingerprintService
в обработку сообщений. Результат проверки отпечатка может быть сохранён
вместе с рейтингом сообщения и включён в отрисовку вывода.

Пример потока:
    1. Пользователь отправляет сообщение боту
    2. Обработчик сообщений получает его
    3. Вызывается OwnerFingerprintService.check()
    4. Результат содержит owner_rating (50 или 1 в MVP)
    5. Этот рейтинг включается в футер сообщения
    6. Пользователь видит "Рейтинг владельца: 50" или "Рейтинг владельца: 1"
"""

# Пример будущей реализации:
#
# from services.owner_fingerprint_service import RandomOwnerFingerprintService
# from aiogram.types import Message
#
# fingerprint_service = RandomOwnerFingerprintService()
#
# async def process_incoming_message(message: Message) -> None:
#     # Проверяем отпечаток владельца
#     owner_result = await fingerprint_service.check(message)
#
#     # Теперь у нас есть:
#     # - owner_result.status (FOUND или NOT_FOUND)
#     # - owner_result.owner_rating (50 или 1)
#
#     # Рендерим сообщение с показом рейтинга владельца
#     message_text = (
#         f"{message.text}\n\n"
#         f"Рейтинг владельца: {owner_result.owner_rating}"
#     )
#
#     await message.answer(message_text)
