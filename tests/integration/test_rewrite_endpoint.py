import pytest
from httpx import AsyncClient
from fastapi import status

# Import the app instance for the test client
# Make sure PYTHONPATH includes the project root or adjust imports
from app.main import app
from app.core.config import settings

# Use pytest-asyncio decorator if test functions are async
@pytest.mark.asyncio
async def test_rewrite_endpoint_success_stub():
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {"text": "Hello world", "style": "pirate"}
        response = await client.post("/v1/rewrite", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["original_text"] == "Hello world"
    assert data["style"] == "pirate"
    # Check stub format (adjust if StubLLMAdapter changes)
    assert data["rewritten_text"] == "[* pirate *] Hello world [* /pirate *]"

@pytest.mark.asyncio
async def test_rewrite_endpoint_default_style():
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {"text": "Formal test"}
        # 'style' is omitted, should default to 'formal'
        response = await client.post("/v1/rewrite", json=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["original_text"] == "Formal test"
    assert data["style"] == "formal"
    assert data["rewritten_text"] == "[* formal *] Formal test [* /formal *]"

@pytest.mark.asyncio
async def test_rewrite_endpoint_invalid_style():
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {"text": "Test", "style": "invalid_style"}
        response = await client.post("/v1/rewrite", json=payload)

    # Pydantic validation results in 422 Unprocessable Entity
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_rewrite_endpoint_text_too_long():
    long_text = "a" * (settings.MAX_TEXT_LENGTH + 1)
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {"text": long_text, "style": "formal"}
        response = await client.post("/v1/rewrite", json=payload)

    # Custom dependency check should return 400 Bad Request
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "exceeds maximum length" in data["detail"]

@pytest.mark.asyncio
async def test_health_check_endpoint():
     async with AsyncClient(app=app, base_url="http://test") as client:
        # Assuming default stub adapter which is always healthy
        response = await client.get("/health")

     assert response.status_code == status.HTTP_200_OK
     data = response.json()
     assert data["status"] == "ok"
     assert data["llm_adapter_status"] == "ok" # Based on StubLLMAdapter

@pytest.mark.asyncio
async def test_health_check_endpoint_unhealthy_adapter(monkeypatch, mocker):
    # Simulate an unhealthy adapter check
    mock_adapter = AsyncMock(spec=LLMAdapter)
    mock_adapter.health_check.return_value = False
    # Patch the singleton instance used by the dependency
    mocker.patch('app.llm.adapters.llm_adapter_instance', return_value=mock_adapter)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK # Or 503 if you change the health endpoint logic
    data = response.json()
    assert data["status"] == "ok" # Or "degraded" depending on health check logic
    assert data["llm_adapter_status"] == "degraded"

@pytest.mark.asyncio
async def test_health_check_endpoint_adapter_error(monkeypatch, mocker):
    # Simulate an error during adapter health check
    mock_adapter = AsyncMock(spec=LLMAdapter)
    mock_adapter.health_check.side_effect = Exception("LLM Connection Down")
    # Patch the singleton instance used by the dependency
    mocker.patch('app.llm.adapters.llm_adapter_instance', return_value=mock_adapter)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["status"] == "error"
    assert data["llm_adapter_status"] == "error"

