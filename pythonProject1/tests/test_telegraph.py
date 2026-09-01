import pytest

import pythonProject1.bot as bot_module

# Простые фейковые асинхронные контексты/ответы для моков
class FakeResp:
    def __init__(self, status, content=None):
        self.status = status
        self._content = content

    async def read(self):
        return self._content

    async def json(self):
        return self._content

class FakeCM:
    def __init__(self, resp):
        self.resp = resp

    async def __aenter__(self):
        return self.resp

    async def __aexit__(self, exc_type, exc, tb):
        return False

class FakeSession:
    def __init__(self, get_resp=None, post_resp=None):
        self.get_resp = get_resp
        self.post_resp = post_resp

    def get(self, url):
        return FakeCM(self.get_resp)

    def post(self, url, data):
        return FakeCM(self.post_resp)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

@pytest.mark.asyncio
async def test_upload_photo_success(monkeypatch):
    # Telegram отдаёт байты, telegra.ph возвращает список с {'src': '/file.jpg'}
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, [{'src': '/file.jpg'}])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url == 'https://telegra.ph/file.jpg'

@pytest.mark.asyncio
async def test_upload_photo_get_fail(monkeypatch):
    # Telegram возвращает 404 -> функция должна вернуть None
    get_resp = FakeResp(404, None)
    post_resp = FakeResp(200, [{'src': '/file.jpg'}])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None

@pytest.mark.asyncio
async def test_upload_photo_telegraph_post_fail(monkeypatch):
    # Telegram OK, но telegra.ph отвечает ошибкой -> None
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(500, None)

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None