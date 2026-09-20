"""Модуль загрузки изображений в imgbb и их подготовки для Telegram."""

import inspect
import logging
from typing import Optional

import aiohttp
from aiogram import Bot

logger = logging.getLogger(__name__)


async def _maybe_await(obj):
    """Если объект awaitable, дождаться его; иначе вернуть как есть."""
    if inspect.isawaitable(obj):
        return await obj
    return obj


async def upload_photo_to_imgbb(
    photo_data: bytes,
    api_key: str,
    session: Optional[aiohttp.ClientSession] = None,
) -> Optional[str]:
    """Загрузить байты изображения в imgbb и вернуть публичную ссылку."""
    if not photo_data or not api_key:
        logger.warning("Photo data or API key is empty")
        return None

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        form = aiohttp.FormData()
        form.add_field("image", photo_data)

        url = f"https://api.imgbb.com/1/upload?key={api_key}"
        resp_ctx = session.post(url, data=form)
        resp_ctx = await _maybe_await(resp_ctx)
        async with resp_ctx as resp:
            if resp.status == 200:
                result = await resp.json()
                if result.get("success"):
                    image_url = result.get("data", {}).get("url")
                    if image_url:
                        logger.info("Uploaded to imgbb: %s", image_url)
                        return image_url
                else:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    logger.error("imgbb upload error: %s", error_msg)
            else:
                logger.error("imgbb returned status %s", resp.status)
    except Exception as exc:
        logger.error("Error uploading to imgbb: %s", exc, exc_info=True)
    finally:
        if close_session and session is not None:
            await session.close()

    return None


async def get_and_upload_photo_to_imgbb(
    file_path: str,
    bot_token: str,
    api_key: str,
    session: Optional[aiohttp.ClientSession] = None,
) -> Optional[str]:
    """Скачать файл из Telegram CDN и затем загрузить в imgbb."""
    if not file_path or not bot_token or not api_key:
        logger.warning("file_path, bot_token or api_key is empty")
        return None

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        logger.info("Downloading photo from Telegram: %s", file_path)

        resp_ctx = session.get(file_url)
        resp_ctx = await _maybe_await(resp_ctx)
        async with resp_ctx as resp:
            if resp.status != 200:
                logger.error("Failed to download photo from Telegram: %s", resp.status)
                return None

            photo_data = await resp.read()
            if not photo_data:
                logger.error("Downloaded photo data is empty")
                return None

            logger.info("Downloaded %d bytes from Telegram", len(photo_data))

            image_url = await upload_photo_to_imgbb(photo_data, api_key, session=session)
            if image_url:
                logger.info("Successfully uploaded to imgbb: %s", image_url)
                return image_url
            logger.error("Failed to upload photo to imgbb")
            return None
    except Exception as exc:
        logger.error("Error in get_and_upload_photo_to_imgbb: %s", exc, exc_info=True)
    finally:
        if close_session and session is not None:
            await session.close()

    return None


async def upload_telegram_file_to_imgbb(
    bot: Bot,
    file_id: str,
    api_key: str,
    session: Optional[aiohttp.ClientSession] = None,
) -> Optional[str]:
    """Загрузить файл Telegram в imgbb через API бота или CDN."""
    if not bot or not file_id or not api_key:
        logger.warning("bot, file_id or api_key is empty")
        return None

    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True

    try:
        file_info = await bot.get_file(file_id)
        file_path = getattr(file_info, "file_path", None)
        if not file_path:
            logger.error("No file_path returned from Bot.get_file()")
            return None

        logger.info("Downloading file via aiogram helper: %s", file_path)

        photo_data: Optional[bytes] = None

        download_attr = getattr(bot, "download_file", None)
        if callable(download_attr):
            try:
                downloaded = await bot.download_file(file_path)
                if isinstance(downloaded, (bytes, bytearray)):
                    photo_data = bytes(downloaded)
                else:
                    read = getattr(downloaded, "read", None)
                    if read is not None and callable(read):
                        maybe = await downloaded.read()
                        if isinstance(maybe, (bytes, bytearray)):
                            photo_data = bytes(maybe)
            except Exception as exc:
                logger.warning("aiogram's download_file failed: %s; falling back to CDN download", exc)

        if photo_data is None:
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
            logger.info("Falling back to CDN download: %s", file_url)

            resp_ctx = session.get(file_url)
            resp_ctx = await _maybe_await(resp_ctx)
            async with resp_ctx as resp:
                if resp.status != 200:
                    logger.error("Failed to download photo from Telegram CDN: %s", resp.status)
                    return None
                photo_data = await resp.read()

        if not photo_data:
            logger.error("Downloaded photo data is empty")
            return None

        logger.info("Downloaded %d bytes", len(photo_data))

        form = aiohttp.FormData()
        form.add_field("image", photo_data)
        resp_ctx = session.post("https://api.imgbb.com/1/upload?key={api_key}", data=form)
        resp_ctx = await _maybe_await(resp_ctx)
        async with resp_ctx as resp:
            if resp.status == 200:
                result = await resp.json()
                if result.get("success"):
                    image_url = result.get("data", {}).get("url")
                    if image_url:
                        logger.info("Successfully uploaded to imgbb: %s", image_url)
                        return image_url
                else:
                    logger.error("Failed to upload photo to imgbb")
                    return None
            else:
                logger.error("imgbb returned status %s", resp.status)
                return None
    except Exception as exc:
        logger.error("Error in upload_telegram_file_to_imgbb: %s", exc, exc_info=True)
    finally:
        if close_session and session is not None:
            await session.close()

    return None
