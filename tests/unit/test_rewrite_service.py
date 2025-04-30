import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.rewriter import RewriteService
from app.llm.adapters import StubLLMAdapter
from app.core.config import settings

@pytest.fixture
def mock_llm_adapter():
    mock = AsyncMock(spec=StubLLMAdapter) # Use spec for type safety
    mock.rewrite.return_value = "Mocked rewrite result"
    return mock

@pytest.fixture
def rewrite_service(mock_llm_adapter):
    # Ensure cache is off for basic tests unless specified
    with patch('app.services.rewriter.settings.CACHE_ENABLED', False):
        service = RewriteService(llm_adapter=mock_llm_adapter)
        yield service # Use yield to allow cleanup if needed

@pytest.mark.asyncio
async def test_rewrite_text_calls_adapter(rewrite_service, mock_llm_adapter):
    text = "Test input"
    style = "formal"
    result = await rewrite_service.rewrite_text(text, style)

    mock_llm_adapter.rewrite.assert_awaited_once_with(text, style)
    assert result == "Mocked rewrite result"

# --- Caching Tests (Stretch Goal) ---

@pytest.fixture
def cached_rewrite_service(mock_llm_adapter):
     # Force enable cache for this test fixture
    with patch('app.services.rewriter.settings.CACHE_ENABLED', True), \
         patch('app.services.rewriter.rewrite_cache', MagicMock()): # Mock the cache instance if needed
        # Re-initialize service with caching conceptually enabled
        # NOTE: Due to how the decorator is applied in the class, we might need
        # to patch 'cachetools.cached' or test via integration test primarily.
        # Let's assume the mechanism works and test the interaction pattern.
        service = RewriteService(llm_adapter=mock_llm_adapter)
        # Clear cache before test if using a real cache instance mock
        if hasattr(service, '_rewrite_decorator'): # Check if using the complex method
             if hasattr(service._rewrite_decorator.__closure__[0].cell_contents, 'cache_clear'):
                 service._rewrite_decorator.__closure__[0].cell_contents.cache_clear()
        yield service


@pytest.mark.asyncio
@patch('app.services.rewriter.settings.CACHE_ENABLED', True) # Ensure cache is seen as enabled
@patch('app.services.rewriter.rewrite_cache') # Mock the cache object directly
async def test_rewrite_text_cache_hit(mock_cache, mock_llm_adapter):
    # Setup mock cache behavior
    cache_store = {}
    def mock_cache_get(key, default=None):
        return cache_store.get(key, default)
    def mock_cache_set(key, value):
        cache_store[key] = value
    mock_cache.__contains__ = MagicMock(side_effect=lambda key: key in cache_store)
    mock_cache.__getitem__ = MagicMock(side_effect=mock_cache_get)
    mock_cache.__setitem__ = MagicMock(side_effect=mock_cache_set)

    # Patch the cache instance used by the @cached decorator
    with patch('cachetools.TTLCache', return_value=mock_cache):
        # We need to instantiate the service *after* patching
        service = RewriteService(llm_adapter=mock_llm_adapter)

        text = "Cache me"
        style = "pirate"

        # First call - should call LLM and cache the result
        mock_llm_adapter.rewrite.return_value = "Arr, cached plunder!"
        result1 = await service.rewrite_text(text, style)
        assert result1 == "Arr, cached plunder!"
        mock_llm_adapter.rewrite.assert_awaited_once_with(text, style)
        # Check if it was added to the (mocked) cache
        assert len(cache_store) == 1


        # Second call - should hit the cache, LLM should NOT be called again
        mock_llm_adapter.reset_mock() # Reset call count
        result2 = await service.rewrite_text(text, style)

        assert result2 == "Arr, cached plunder!" # Should get cached value
        mock_llm_adapter.rewrite.assert_not_awaited() # IMPORTANT: Check it wasn't called
