
import pytest
from app.llm.adapters import StubLLMAdapter, OpenAILLMAdapter, AnthropicLLMAdapter, get_llm_adapter
from app.llm.interface import LLMAdapter
from app.core.config import Settings

@pytest.mark.asyncio
async def test_stub_llm_adapter_rewrite():
    adapter = StubLLMAdapter()
    result = await adapter.rewrite("Hello", "pirate")
    assert result == "[* pirate *] Hello [* /pirate *]"
    assert adapter.health_check() is True

# Parameterize tests for different adapters if needed
# Test API key handling (requires mocking os.getenv or using monkeypatch)
def test_get_llm_adapter_stub_default(monkeypatch):
    # Ensure no env vars are set that would select another provider
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    adapter = get_llm_adapter()
    assert isinstance(adapter, StubLLMAdapter)

def test_get_llm_adapter_openai_no_key(monkeypatch, caplog):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    adapter = get_llm_adapter()
    assert isinstance(adapter, StubLLMAdapter) # Falls back to stub
    assert "OpenAI provider selected but no LLM_API_KEY found" in caplog.text

def test_get_llm_adapter_openai_with_key(monkeypatch, mocker):
    # Mock the openai package import check if needed
    mocker.patch('importlib.import_module', return_value=True) # Simulate package exists
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    adapter = get_llm_adapter()
    assert isinstance(adapter, OpenAILLMAdapter)
    assert adapter.api_key == "fake-key"
    assert adapter.health_check() is True

# Add similar tests for Anthropic
