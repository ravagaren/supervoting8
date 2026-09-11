"""Utilities for uploading images to imgbb.

This module contains the functions that were previously defined inside
pythonProject1/bot.py. They have been moved here to separate network/IO
responsibilities from bot handlers.

Functions:
- upload_photo_to_imgbb(photo_data: bytes, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]
- get_and_upload_photo_to_imgbb(file_path: str, bot_token: str, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]
- upload_telegram_file_to_imgbb(bot: Bot, file_id: str, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]

The new upload_telegram_file_to_imgbb uses aiogram's Bot API to obtain the
file metadata and attempts to download the file via aiogram's download
helper when available. If aiogram's helper isn't available it falls back to
downloading the file from Telegram CDN using the bot token.

These functions accept an optional aiohttp.ClientSession. If no session is
passed, a temporary session will be created and closed by the function.

They do not depend on the global config or bot objects so they can be
unit-tested and reused from other modules.
"""

import aiohttp
import logging
import inspect
from typing import Optional

from aiogram import Bot

logger = logging.getLogger(__name__)


async def _maybe_await(obj):
    """Await obj if it's awaitable, otherwise return as-is."""
    if inspect.isawaitable(obj):
        return await obj
    return obj


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
        # support session.post being either a regular function returning an
        # async-context-manager or an awaitable (AsyncMock) returning such
        resp_ctx = session.post(url, data=form)
        resp_ctx = await _maybe_await(resp_ctx)
        async with resp_ctx as resp:
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
    (Deprecated) Download a file from Telegram CDN using the provided file_path and bot_token,
    then upload it to imgbb and return the permanent URL.

    Kept for backward compatibility. Prefer upload_telegram_file_to_imgbb which
    uses aiogram's Bot API for downloading.
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

        resp_ctx = session.get(file_url)
        resp_ctx = await _maybe_await(resp_ctx)
        async with resp_ctx as resp:
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


async def upload_telegram_file_to_imgbb(bot: Bot, file_id: str, api_key: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
    """
    Download a file using aiogram's Bot API (preferred) and upload it to imgbb.

    Args:
        bot: aiogram.Bot instance used to download the file.
        file_id: Telegram file_id for the file to download.
        api_key: imgbb API key used to upload the file.
        session: Optional aiohttp.ClientSession for HTTP uploads/downloads.

    Returns:
        Permanent imgbb URL on success, or None on failure.
    """
    if not bot or not file_id or not api_key:
        logger.warning("bot, file_id or api_key is empty")
        return None

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        # Use aiogram to get file metadata first
        file_info = await bot.get_file(file_id)
        file_path = getattr(file_info, 'file_path', None)
        if not file_path:
            logger.error('No file_path returned from Bot.get_file()')
            return None

        logger.info(f'Downloading file via aiogram helper: {file_path}')

        photo_data: Optional[bytes] = None

        # Preferred path: use aiogram's download helper if present
        download_attr = getattr(bot, 'download_file', None)
        if callable(download_attr):
            try:
                downloaded = await bot.download_file(file_path)
                # downloaded can be bytes or an object with .read()
                if isinstance(downloaded, (bytes, bytearray)):
                    photo_data = bytes(downloaded)
                else:
                    # treat as file-like
                    read = getattr(downloaded, 'read', None)
                    if read is not None and callable(read):
                        maybe = await downloaded.read()
                        if isinstance(maybe, (bytes, bytearray)):
                            photo_data = bytes(maybe)
            except Exception as e:
                logger.warning(f"aiogram's download_file failed: {e}; falling back to CDN download")

        # Fallback: download from Telegram CDN using bot.token
        if photo_data is None:
            file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_path}'
            logger.info(f'Falling back to CDN download: {file_url}')

            resp_ctx = session.get(file_url)
            resp_ctx = await _maybe_await(resp_ctx)
            async with resp_ctx as resp:
                if resp.status != 200:
                    logger.error(f"Failed to download photo from Telegram CDN: {resp.status}")
                    return None
                photo_data = await resp.read()

        if not photo_data:
            logger.error("Downloaded photo data is empty")
            return None

        logger.info(f'Downloaded {len(photo_data)} bytes')

        # Prepare and send upload request
        form = aiohttp.FormData()
        form.add_field('image', photo_data)
        resp_ctx = session.post(f'https://api.imgbb.com/1/upload?key={api_key}', data=form)
        resp_ctx = await _maybe_await(resp_ctx)
        async with resp_ctx as resp:
            if resp.status == 200:
                result = await resp.json()
                if result.get('success'):
                    image_url = result.get('data', {}).get('url')
                    if image_url:
                        logger.info(f'Successfully uploaded to imgbb: {image_url}')
                        return image_url
                else:
                    logger.error('Failed to upload photo to imgbb')
                    return None
            else:
                logger.error(f'imgbb returned status {resp.status}')
                return None

    except Exception as e:
        logger.error(f"Error in upload_telegram_file_to_imgbb: {e}", exc_info=True)

    finally:
        if close_session and session is not None:
            await session.close()

    return None
