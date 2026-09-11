import pytest
from unittest.mock import AsyncMock, MagicMock
import aiohttp

from utils.imgbb import upload_photo_to_imgbb, get_and_upload_photo_to_imgbb


class MockResp:
    def __init__(self, status=200, json_data=None, read_data: bytes = b""):
        self.status = status
        self._json = json_data or {}
        self._read = read_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._json

    async def read(self):
        return self._read


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_success():
    session = MagicMock(spec=aiohttp.ClientSession)
    # session.post will be awaited (it's an AsyncMock), and should return an object
    # that works as an async context manager (MockResp implements __aenter__)
    session.post = AsyncMock(return_value=MockResp(200, {"success": True, "data": {"url": "https://imgbb/test.jpg"}}))

    url = await upload_photo_to_imgbb(b"image-bytes", "API_KEY", session=session)
    assert url == "https://imgbb/test.jpg"


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_failure_no_api_key():
    session = MagicMock(spec=aiohttp.ClientSession)
    url = await upload_photo_to_imgbb(b"image-bytes", "", session=session)
    assert url is None


@pytest.mark.asyncio
async def test_get_and_upload_photo_to_imgbb_success():
    session = MagicMock(spec=aiohttp.ClientSession)

    # mock download response (telegram file)
    session.get = AsyncMock(return_value=MockResp(200, None, read_data=b"img-bytes"))
    # mock upload response (imgbb)
    session.post = AsyncMock(return_value=MockResp(200, {"success": True, "data": {"url": "https://imgbb/uploaded.jpg"}}))

    url = await get_and_upload_photo_to_imgbb("path/to/file.jpg", "BOT_TOKEN", "IMGBB_KEY", session=session)
    assert url == "https://imgbb/uploaded.jpg"


@pytest.mark.asyncio
async def test_get_and_upload_photo_to_imgbb_failure_download():
    session = MagicMock(spec=aiohttp.ClientSession)
    session.get = AsyncMock(return_value=MockResp(404, None, read_data=b""))

    url = await get_and_upload_photo_to_imgbb("path/to/file.jpg", "BOT_TOKEN", "IMGBB_KEY", session=session)
    assert url is None
