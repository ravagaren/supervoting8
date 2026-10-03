"""Tests for author profile service."""

import pytest

from services.author_profile_service import AuthorProfileService


@pytest.fixture
def service() -> AuthorProfileService:
    return AuthorProfileService()


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
async def test_resolve_owner_with_profile(service: AuthorProfileService) -> None:
    """Test that valid profile returns rating 50."""
    profile = "Имя: Анна\nВозраст: 28\nГород: Москва"
    rating = await service.resolve_owner(profile)
    assert rating == 50


@pytest.mark.asyncio
async def test_resolve_owner_consistency(service: AuthorProfileService) -> None:
    """Test that same profile always returns same rating."""
    profile = "Тестовый профиль"
    rating1 = await service.resolve_owner(profile)
    rating2 = await service.resolve_owner(profile)
    assert rating1 == rating2


@pytest.mark.asyncio
async def test_get_profile_info(service: AuthorProfileService) -> None:
    """Test get_profile_info returns AuthorProfile."""
    profile = "Имя: Анна\nВозраст: 28"
    info = await service.get_profile_info(profile)

    assert info is not None
    assert info.profile_text == profile
    assert len(info.profile_hash) == 64
    assert info.owner_rating == 50


def test_normalize_profile(service: AuthorProfileService) -> None:
    """Test profile normalization."""
    profile = "  Имя:   Анна  \n\n  Возраст:  28  "
    normalized = service._normalize_profile(profile)

    assert normalized == "Имя: Анна Возраст: 28"
    assert "\n" not in normalized


def test_lookup_owner_rating(service: AuthorProfileService) -> None:
    """Test lookup returns consistent rating."""
    hash1 = "abc123"
    hash2 = "def456"

    rating1 = service._lookup_owner_rating(hash1)
    rating2 = service._lookup_owner_rating(hash2)

    assert rating1 == 50
    assert rating2 == 50
