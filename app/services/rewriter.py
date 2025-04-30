import logging

from cachetools import TTLCache, cached
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

    # Apply caching conditionally using a decorator factory
    def _rewrite_decorator(self, func):
        if settings.CACHE_ENABLED and rewrite_cache is not None:
            # key=hashkey ignores the 'self' argument for caching
            return cached(
                cache=rewrite_cache,
                key=lambda self, text, style: hashkey(text, style),
            )(func)
        else:
            # Return the original function if caching is disabled
            return func

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
            logger.info(
                f"Performing rewrite for style '{inner_style}' (Cache {'hit' if settings.CACHE_ENABLED and hashkey(inner_text, inner_style) in rewrite_cache else 'miss/disabled'})"
            )
            # In a real scenario, add more robust error handling here
            try:
                rewritten_text = await inner_self.llm_adapter.rewrite(
                    inner_text, inner_style
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

        # Apply the decorator (or not) and call the inner function
        decorated_rewrite = self._rewrite_decorator(_perform_rewrite)
        return await decorated_rewrite(self, text, style)


# Instantiate the service with the singleton adapter
# This can be used for dependency injection
rewrite_service_instance = RewriteService(llm_adapter=llm_adapter_instance)
