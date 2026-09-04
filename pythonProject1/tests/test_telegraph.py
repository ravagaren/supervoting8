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
async def test_upload_photo_to_imgbb_success(monkeypatch):
    """Test successful photo upload to imgbb with correct response format."""
    # Telegram отдаёт байты, imgbb возвращает JSON с прямой ссылкой
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, {
        'success': True,
        'data': {
            'url': 'https://i.imgbb.com/abc123xyz.jpg',
            'delete_url': 'https://imgbb.com/delete/abc123'
        }
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', 'FAKE_IMGBB_KEY')
    assert url == 'https://i.imgbb.com/abc123xyz.jpg'


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_none_api_key(monkeypatch):
    """Test when API key is None - should return None."""
    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', None)
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_empty_api_key(monkeypatch):
    """Test when API key is empty string - should return None."""
    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', '')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_imgbb_error_response(monkeypatch):
    """Test when imgbb returns error response."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, {
        'success': False,
        'error': {
            'message': 'Invalid image file'
        }
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', 'FAKE_IMGBB_KEY')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_imgbb_bad_status(monkeypatch):
    """Test when imgbb returns non-200 status."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(401, {
        'error': {
            'message': 'Invalid API key'
        }
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', 'INVALID_KEY')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_missing_url_in_response(monkeypatch):
    """Test when imgbb response is missing 'url' field."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, {
        'success': True,
        'data': {
            'delete_url': 'https://imgbb.com/delete/abc123'
            # Missing 'url' field
        }
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', 'FAKE_IMGBB_KEY')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_none_response(monkeypatch):
    """Test when imgbb returns None - should return None."""
    get_resp = FakeResp(200, b'fake-image-bytes')
    post_resp = FakeResp(200, None)

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', 'FAKE_IMGBB_KEY')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_exception_handling(monkeypatch):
    """Test exception handling during upload."""
    def failing_session():
        raise RuntimeError("Network error")

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        failing_session
    )

    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', 'FAKE_IMGBB_KEY')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_timeout(monkeypatch):
    """Test handling of timeout during imgbb upload."""
    class TimeoutSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            raise asyncio.TimeoutError("Request timeout")

        def post(self, url, data=None, **kwargs):
            raise asyncio.TimeoutError("Request timeout")

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        TimeoutSession
    )

    url = await bot_module.upload_photo_to_imgbb(b'fake-image-bytes', 'FAKE_IMGBB_KEY')
    assert url is None


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_large_file(monkeypatch):
    """Test uploading large photo data."""
    # imgbb supports files up to 32MB
    large_photo_data = b'x' * (5 * 1024 * 1024)  # 5MB
    
    get_resp = FakeResp(200, large_photo_data)
    post_resp = FakeResp(200, {
        'success': True,
        'data': {
            'url': 'https://i.imgbb.com/large_file_abc123.jpg'
        }
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_imgbb(large_photo_data, 'FAKE_IMGBB_KEY')
    assert url == 'https://i.imgbb.com/large_file_abc123.jpg'


@pytest.mark.asyncio
async def test_upload_photo_to_imgbb_small_file(monkeypatch):
    """Test uploading very small photo data."""
    small_photo_data = b'x'  # 1 byte
    
    get_resp = FakeResp(200, small_photo_data)
    post_resp = FakeResp(200, {
        'success': True,
        'data': {
            'url': 'https://i.imgbb.com/small_abc123.jpg'
        }
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.upload_photo_to_imgbb(small_photo_data, 'FAKE_IMGBB_KEY')
    assert url == 'https://i.imgbb.com/small_abc123.jpg'


@pytest.mark.asyncio
async def test_get_and_upload_photo_telegram_fail(monkeypatch):
    """Test when Telegram returns error during file download."""
    get_resp = FakeResp(404, None)
    post_resp = FakeResp(200, {
        'success': True,
        'data': {'url': 'https://i.imgbb.com/test.jpg'}
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.get_and_upload_photo_to_imgbb('documents/photo.jpg', 'FAKE_TOKEN')
    assert url is None


@pytest.mark.asyncio
async def test_get_and_upload_photo_success(monkeypatch):
    """Test full flow: get photo from Telegram, then upload to imgbb."""
    get_resp = FakeResp(200, b'telegram-photo-bytes')
    post_resp = FakeResp(200, {
        'success': True,
        'data': {
            'url': 'https://i.imgbb.com/telegram_photo_xyz.jpg',
            'expiration': 15552000  # Expiration in seconds (6 months)
        }
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.get_and_upload_photo_to_imgbb('documents/photo.jpg', 'FAKE_TOKEN')
    assert url == 'https://i.imgbb.com/telegram_photo_xyz.jpg'


@pytest.mark.asyncio
async def test_get_and_upload_photo_imgbb_fail(monkeypatch):
    """Test when Telegram OK but imgbb upload fails."""
    get_resp = FakeResp(200, b'telegram-photo-bytes')
    post_resp = FakeResp(200, {
        'success': False,
        'error': {'message': 'Upload failed'}
    })

    monkeypatch.setattr(
        bot_module.aiohttp, "ClientSession",
        lambda: FakeSession(get_resp=get_resp, post_resp=post_resp)
    )

    url = await bot_module.get_and_upload_photo_to_imgbb('documents/photo.jpg', 'FAKE_TOKEN')
    assert url is None
