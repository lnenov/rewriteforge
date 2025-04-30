from abc import ABC, abstractmethod

class LLMAdapter(ABC):
    """Abstract Base Class for LLM Adapters"""

    @abstractmethod
    async def rewrite(self, text: str, style: str) -> str:
        """Rewrites the given text in the specified style."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks if the adapter is configured and potentially reachable."""
        # Basic check by default, can be overridden for real API checks
        return True
