from aiogram import Router
from aiogram.filters import Command
from aiogram.types import LinkPreviewOptions, Message
from utils.usefull_utils import generate_test_content_message

router = Router()
options_4 = LinkPreviewOptions(prefer_large_media=True, show_above_text=True)


@router.message(Command("start", ignore_case=True))
async def start(message: Message) -> None:
    await message.answer("Use /Test")


@router.message(Command("test", ignore_case=True))
async def test(message: Message) -> None:
    content = await generate_test_content_message()
    await message.answer(**content.as_kwargs(), link_preview_options=options_4)
