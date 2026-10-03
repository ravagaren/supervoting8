"""Tests for author profile service."""

import pytest

from services.author_profile_service import AuthorProfileService
from state_manager import state_manager, AuthorRating


@pytest.fixture
def service() -> AuthorProfileService:
    """Create a fresh AuthorProfileService for each test."""
    return AuthorProfileService()


@pytest.fixture(autouse=True)
def reset_state_manager():
    """Reset state manager before each test."""
    state_manager.reset()
    yield
    state_manager.reset()


@pytest.mark.asyncio
async def test_resolve_owner_none_profile(service: AuthorProfileService) -> None:
    """Test that None profile returns rating 1."""
    rating = await service.resolve_owner(None)
    assert rating == 1


@pytest.mark.asyncio
async def test_resolve_owner_empty_profile(service: AuthorProfileService) -> None:
    """Test that empty profile returns rating 1."""
    rating = await service.resolve_owner("")
    assert rating == 1


@pytest.mark.asyncio
async def test_resolve_owner_with_profile_new_author(service: AuthorProfileService) -> None:
    """Test that new profile returns rating 10 (initial rating for new author)."""
    profile = "Имя: Анна\nВозраст: 28\nГород: Москва"
    rating = await service.resolve_owner(profile)
    # Новый автор инициализируется с рейтингом 10
    assert rating == 10


@pytest.mark.asyncio
async def test_resolve_owner_with_profile_known_author(service: AuthorProfileService) -> None:
    """Test that known author returns their saved rating."""
    profile = "Имя: Анна\nВозраст: 28\nГород: Москва"
    
    # Сначала сохраняем рейтинг автора в StateManager с message_count > 0 (чтобы он не был новым)
    profile_hash = service._compute_hash(service._normalize_profile(profile))
    known_rating = AuthorRating(owner_rating=75, message_count=5, avg_content_rating=60.0)
    state_manager.set_author_rating(profile_hash, known_rating)
    
    # Теперь получаем рейтинг
    rating = await service.resolve_owner(profile)
    assert rating == 75


@pytest.mark.asyncio
async def test_resolve_owner_consistency(service: AuthorProfileService) -> None:
    """Test that same profile always returns same rating."""
    profile = "Тестовый профиль"
    rating1 = await service.resolve_owner(profile)
    rating2 = await service.resolve_owner(profile)
    assert rating1 == rating2
    # Обе должны быть 10 (инициальный рейтинг)
    assert rating1 == 10


@pytest.mark.asyncio
async def test_get_profile_info_new_author(service: AuthorProfileService) -> None:
    """Test get_profile_info returns AuthorProfile for new author."""
    profile = "Имя: Анна\nВозраст: 28"
    info = await service.get_profile_info(profile)

    assert info is not None
    assert info.profile_text == profile
    assert len(info.profile_hash) == 64
    # Новый автор инициализируется с рейтингом 10
    assert info.owner_rating == 10


@pytest.mark.asyncio
async def test_get_profile_info_known_author(service: AuthorProfileService) -> None:
    """Test get_profile_info returns correct rating for known author."""
    profile = "Имя: Анна\nВозраст: 28"
    
    # Сначала сохраняем рейтинг с message_count > 0
    profile_hash = service._compute_hash(service._normalize_profile(profile))
    known_rating = AuthorRating(owner_rating=50, message_count=3, avg_content_rating=45.0)
    state_manager.set_author_rating(profile_hash, known_rating)
    
    info = await service.get_profile_info(profile)
    assert info is not None
    assert info.owner_rating == 50


def test_normalize_profile(service: AuthorProfileService) -> None:
    """Test profile normalization."""
    profile = "  Имя:   Анна  \n\n  Возраст:  28  "
    normalized = service._normalize_profile(profile)

    assert normalized == "Имя: Анна Возраст: 28"
    assert "\n" not in normalized


def test_normalize_profile_empty(service: AuthorProfileService) -> None:
    """Test normalization of empty profile."""
    normalized = service._normalize_profile("")
    assert normalized == ""
    
    normalized = service._normalize_profile(None)
    assert normalized == ""


def test_compute_hash_consistency(service: AuthorProfileService) -> None:
    """Test that same text produces same hash."""
    text1 = "Имя: Анна"
    text2 = "Имя: Анна"
    
    hash1 = service._compute_hash(text1)
    hash2 = service._compute_hash(text2)
    
    assert hash1 == hash2
    assert len(hash1) == 64


def test_compute_hash_different_text(service: AuthorProfileService) -> None:
    """Test that different text produces different hash."""
    text1 = "Имя: Анна"
    text2 = "Имя: Борис"
    
    hash1 = service._compute_hash(text1)
    hash2 = service._compute_hash(text2)
    
    assert hash1 != hash2


def test_compute_hash_empty(service: AuthorProfileService) -> None:
    """Test compute_hash with empty string."""
    hash_result = service._compute_hash("")
    assert hash_result == ""


@pytest.mark.asyncio
async def test_get_profile_hash(service: AuthorProfileService) -> None:
    """Test get_profile_hash returns valid hash."""
    profile = "Имя: Анна\nВозраст: 28"
    profile_hash = await service.get_profile_hash(profile)
    
    assert profile_hash is not None
    assert len(profile_hash) == 64


@pytest.mark.asyncio
async def test_get_profile_hash_none(service: AuthorProfileService) -> None:
    """Test get_profile_hash returns None for empty profile."""
    profile_hash = await service.get_profile_hash(None)
    assert profile_hash is None
    
    profile_hash = await service.get_profile_hash("")
    assert profile_hash is None


@pytest.mark.asyncio
async def test_get_profile_hash_consistency(service: AuthorProfileService) -> None:
    """Test that same profile always produces same hash."""
    profile = "Тестовый профиль с текстом"
    
    hash1 = await service.get_profile_hash(profile)
    hash2 = await service.get_profile_hash(profile)
    
    assert hash1 == hash2
    assert len(hash1) == 64


@pytest.mark.asyncio
async def test_resolve_owner_initializes_state_manager(service: AuthorProfileService) -> None:
    """Test that resolve_owner initializes author rating in StateManager for new authors."""
    profile = "Новый профиль"
    profile_hash = service._compute_hash(service._normalize_profile(profile))
    
    # Убедиться что автора нет в StateManager
    assert state_manager.get_author_rating(profile_hash).message_count == 0
    
    # Вызвать resolve_owner
    rating = await service.resolve_owner(profile)
    
    # Проверить что рейтинг вернулся
    assert rating == 10
    
    # Проверить что в StateManager теперь есть этот автор
    stored_rating = state_manager.get_author_rating(profile_hash)
    assert stored_rating.owner_rating == 10
    assert stored_rating.message_count == 1
