import logging

from cachetools import TTLCache
from cachetools.keys import hashkey

from app.core.config import settings
from app.llm.adapters import llm_adapter_instance  # Import the singleton
from app.llm.interface import LLMAdapter

logger = logging.getLogger(__name__)

# Initialize cache only if enabled
rewrite_cache = None
if settings.CACHE_ENABLED:
    rewrite_cache = TTLCache(
        maxsize=settings.CACHE_MAX_SIZE, ttl=settings.CACHE_TTL_SECONDS
    )
    logger.info(
        f"In-memory cache enabled: maxsize={settings.CACHE_MAX_SIZE}, ttl={settings.CACHE_TTL_SECONDS}s"
    )
else:
    logger.info("In-memory cache is disabled.")


class RewriteService:
    def __init__(self, llm_adapter: LLMAdapter):
        self.llm_adapter = llm_adapter

    async def rewrite_text(self, text: str, style: str) -> str:
        """
        Rewrites text using the configured LLM adapter.
        Applies caching if enabled.
        """
        # This is slightly convoluted way to apply the cache decorator conditionally
        # We define an inner method that actually calls the LLM
        # and apply the decorator (or not) to it.

        async def _perform_rewrite(
            inner_self, inner_text: str, inner_style: str
        ) -> str:
            # In a real scenario, add more robust error handling here
            if (
                settings.CACHE_ENABLED
                and hashkey(inner_text, inner_style) in rewrite_cache
            ):
                logger.info(f"Rewriting for style '{inner_style}' (Cache hit)")
                return rewrite_cache[hashkey(inner_text, inner_style)]
            else:
                logger.info(
                    f"Rewriting for style '{inner_style}' (Cache miss/disabled)"
                )
                try:
                    rewritten_text = await inner_self.llm_adapter.rewrite(
                        inner_text, inner_style
                    )
                    if settings.CACHE_ENABLED:
                        rewrite_cache[hashkey(inner_text, inner_style)] = (
                            rewritten_text
                        )
                    return rewritten_text
                except ConnectionError as e:
                    logger.error(f"LLM connection error during rewrite: {e}")
                    # Re-raise or handle as appropriate for the API layer
                    raise
                except Exception as e:
                    logger.error(
                        f"Unexpected error during rewrite: {e}", exc_info=True
                    )
                    raise  # Re-raise for higher layers to handle

        return await _perform_rewrite(self, text, style)


# Instantiate the service with the singleton adapter
# This can be used for dependency injection
rewrite_service_instance = RewriteService(llm_adapter=llm_adapter_instance)
