"""Utilities for uploading images to imgbb.

This module contains the functions that were previously defined inside
pythonProject1/bot.py. They have been moved here to separate network/IO
responsibilities from bot handlers.

Two functions:
- upload_photo_to_imgbb(photo_data: bytes, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]
- get_and_upload_photo_to_imgbb(file_path: str, bot_token: str, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]

Both functions accept an optional aiohttp.ClientSession. If no session is
passed, a temporary session will be created and closed by the function.

These functions do not depend on the global config or bot objects so they
can be unit-tested and reused from other modules.
"""

import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def upload_photo_to_imgbb(photo_data: bytes, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
    """
    Upload photo bytes to imgbb and return the permanent URL.

    Args:
        photo_data: Bytes of the image to upload.
        api_key: imgbb API key.
        session: Optional aiohttp.ClientSession. If not provided, a temporary
                 session will be created and closed.

    Returns:
        URL string on success, None on failure.
    """
    if not photo_data or not api_key:
        logger.warning("Photo data or API key is empty")
        return None

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        form = aiohttp.FormData()
        form.add_field('image', photo_data)

        url = f'https://api.imgbb.com/1/upload?key={api_key}'
        async with session.post(url, data=form) as resp:
            if resp.status == 200:
                result = await resp.json()
                if result.get('success'):
                    image_url = result.get('data', {}).get('url')
                    if image_url:
                        logger.info(f'Uploaded to imgbb: {image_url}')
                        return image_url
                else:
                    error_msg = result.get('error', {}).get('message', 'Unknown error')
                    logger.error(f"imgbb upload error: {error_msg}")
            else:
                logger.error(f"imgbb returned status {resp.status}")

    except Exception as e:
        logger.error(f"Error uploading to imgbb: {e}", exc_info=True)

    finally:
        if close_session and session is not None:
            await session.close()

    return None


async def get_and_upload_photo_to_imgbb(file_path: str, bot_token: str, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
    """
    Download a file from Telegram CDN using the provided file_path and bot_token,
    then upload it to imgbb and return the permanent URL.

    Args:
        file_path: Path returned by Bot.get_file (e.g. "photos/file_123.jpg").
        bot_token: Telegram bot token used to download the file.
        api_key: imgbb API key used to upload the file.
        session: Optional aiohttp.ClientSession. If not provided, a temporary
                 session will be created and closed.

    Returns:
        Permanent imgbb URL on success, or None on failure.
    """
    if not file_path or not bot_token or not api_key:
        logger.warning("file_path, bot_token or api_key is empty")
        return None

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        file_url = f'https://api.telegram.org/file/bot{bot_token}/{file_path}'
        logger.info(f'Downloading photo from Telegram: {file_path}')

        async with session.get(file_url) as resp:
            if resp.status != 200:
                logger.error(f"Failed to download photo from Telegram: {resp.status}")
                return None

            photo_data = await resp.read()
            if not photo_data:
                logger.error("Downloaded photo data is empty")
                return None

            logger.info(f'Downloaded {len(photo_data)} bytes from Telegram')

            image_url = await upload_photo_to_imgbb(photo_data, api_key, session=session)
            if image_url:
                logger.info(f'Successfully uploaded to imgbb: {image_url}')
                return image_url
            else:
                logger.error("Failed to upload photo to imgbb")
                return None

    except Exception as e:
        logger.error(f"Error in get_and_upload_photo_to_imgbb: {e}", exc_info=True)

    finally:
        if close_session and session is not None:
            await session.close()

    return None
