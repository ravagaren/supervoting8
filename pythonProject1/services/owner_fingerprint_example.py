"""Example of using owner fingerprint service in a handler.

This module demonstrates how to integrate the OwnerFingerprintService
into message processing. The fingerprint check result can be stored
alongside the message rating and included in the rendered output.

Example flow:
    1. User sends a message to the bot
    2. Message handler receives it
    3. OwnerFingerprintService.check() is called
    4. Result contains owner_rating (50 or 1 for MVP)
    5. This rating is included in the message footer
    6. User sees "Owner rating: 50" or "Owner rating: 1" below the message
"""

# Future implementation example:
#
# from services.owner_fingerprint_service import RandomOwnerFingerprintService
# from aiogram.types import Message
#
# fingerprint_service = RandomOwnerFingerprintService()
#
# async def process_incoming_message(message: Message) -> None:
#     # Check owner fingerprint
#     owner_result = await fingerprint_service.check(message)
#
#     # Now we know:
#     # - owner_result.status (FOUND or NOT_FOUND)
#     # - owner_result.owner_rating (50 or 1)
#
#     # Render message with owner rating shown first
#     message_text = (
#         f"{message.text}\n\n"
#         f"Owner rating: {owner_result.owner_rating}"
#     )
#
#     await message.answer(message_text)
