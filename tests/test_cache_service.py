import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.core.cache import CacheService, cache_result


@pytest.mark.asyncio
async def test_cache_service_availability():
    """Test cache service availability check"""
    with patch("app.core.cache.get_cache") as mock_get_cache:
        # Case 1: Cache not initialized
        mock_get_cache.return_value = None
        service = CacheService()
        assert not service.is_available()

        # Case 2: Cache initialized but disabled
        mock_cache_manager = MagicMock()
        mock_cache_manager.enabled = False
        mock_get_cache.return_value = mock_cache_manager
        service = CacheService()
        assert not service.is_available()

        # Case 3: Cache initialized and enabled
        mock_cache_manager.enabled = True
        mock_cache_manager.redis_client = MagicMock()
        mock_get_cache.return_value = mock_cache_manager
        service = CacheService()
        # Reset internal state to force property re-evaluation
        service.redis = None
        assert service.is_available()


@pytest.mark.asyncio
async def test_cache_operations():
    """Test get/set operations"""
    service = CacheService()
    mock_redis = MagicMock()
    service.redis = mock_redis

    # Test Set
    mock_redis.setex.return_value = True
    result = await service.set("test_key", {"data": "value"})
    assert result is True
    mock_redis.setex.assert_called_once()

    # Test Get
    mock_redis.get.return_value = '{"data": "value"}'
    data = await service.get("test_key")
    assert data == {"data": "value"}

    # Test Delete
    await service.delete("test_key")
    mock_redis.delete.assert_called_with("test_key")


@pytest.mark.asyncio
async def test_cache_decorator():
    """Test cache decorator"""
    mock_service = MagicMock()
    mock_service.is_available.return_value = True

    # Use AsyncMock for async methods or configure MagicMock to be awaitable
    future_none = asyncio.Future()
    future_none.set_result(None)
    mock_service.get.return_value = future_none

    future_true = asyncio.Future()
    future_true.set_result(True)
    mock_service.set.return_value = future_true

    with patch("app.core.cache.cache", mock_service):

        @cache_result(ttl=60)
        async def expensive_operation(x):
            return x * 2

        # First call - should execute function
        result = await expensive_operation(5)
        assert result == 10
        mock_service.set.assert_called_once()

        # Second call - should return cached (mocking cache hit)
        future_ten = asyncio.Future()
        future_ten.set_result(10)
        mock_service.get.return_value = future_ten
        mock_service.set.reset_mock()

        result2 = await expensive_operation(5)
        assert result2 == 10
        mock_service.set.assert_not_called()
