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

    def post(self, url, data=None, **kwargs):
        return FakeCM(self.post_resp)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_upload_photo_success(monkeypatch):
    """Test successful photo upload to Telegraph with correct response format."""
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
    """Test when Telegram returns 404 - function should return None."""
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
    """Test when telegraph returns error status - should return None."""
    # Telegram OK, но telegра.ph отвечает ошибкой -> None
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(500, None)

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_telegraph_empty_list(monkeypatch):
    """Test when telegraph returns empty list - should return None."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, [])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_telegraph_dict_response(monkeypatch):
    """Test when telegraph returns dict instead of list - should return None."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    # Telegraph может вернуть {'error': 'Invalid request'} вместо списка
    post_resp = FakeResp(200, {'error': 'Invalid request'})

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_telegraph_none_response(monkeypatch):
    """Test when telegraph returns None - should return None."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, None)

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_telegraph_missing_src(monkeypatch):
    """Test when telegraph list item doesn't have 'src' key - should return None."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    # Telegraph возвращает список но без ключа 'src'
    post_resp = FakeResp(200, [{'error': 'file upload failed'}])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_exception_handling(monkeypatch):
    """Test exception handling during upload."""
    def failing_session():
        raise RuntimeError("Network error")

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        failing_session
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_telegraph_bad_status_with_list(monkeypatch):
    """Test when telegraph returns 400 with list response - should return None because status != 200."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(400, [{'src': '/file.jpg'}])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_multiple_files_in_response(monkeypatch):
    """Test when telegraph returns multiple files - should use first one."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, [
        {'src': '/file1.jpg'},
        {'src': '/file2.jpg'}
    ])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url == 'https://telegra.ph/file1.jpg'


@pytest.mark.asyncio
async def test_upload_photo_file_path_with_subdirs(monkeypatch):
    """Test correct URL construction with file paths containing subdirectories."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, [{'src': '/photos/2024/abc123.jpg'}])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('documents/photos/2024/file.jpg', 'FAKE_TOKEN')
    assert url == 'https://telegra.ph/photos/2024/abc123.jpg'


@pytest.mark.asyncio
async def test_upload_photo_empty_bytes(monkeypatch):
    """Test when Telegram returns empty bytes - should still attempt telegraph upload."""
    get_resp = FakeResp(200, b'')
    post_resp = FakeResp(200, [{'src': '/file.jpg'}])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url == 'https://telegra.ph/file.jpg'


@pytest.mark.asyncio
async def test_upload_photo_telegraph_returns_empty_src(monkeypatch):
    """Test when telegraph returns empty string in src - should still construct URL."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, [{'src': ''}])

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_telegraph('path/to/file.jpg', 'FAKE_TOKEN')
    assert url == 'https://telegra.ph'
