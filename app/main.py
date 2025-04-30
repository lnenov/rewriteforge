import logging

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse

from app.api.v1.endpoints import rewrite as api_v1_rewrite
from app.core.config import settings
from app.llm.adapters import llm_adapter_instance  # Import the singleton
from app.llm.interface import LLMAdapter

# --- Logging Configuration ---
# Basic logging setup (customize as needed for production)
log_level = logging.DEBUG if settings.RELOAD else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- FastAPI Application ---
app = FastAPI(
    title="RewriteForge Service",
    description="A microservice to rewrite text into different styles.",
    version="0.1.0",
    # Add other OpenAPI metadata if desired
    # docs_url="/api/docs",
    # redoc_url="/api/redoc",
    # openapi_url="/api/v1/openapi.json"
)

# --- Routers ---
app.include_router(api_v1_rewrite.router, prefix="/v1", tags=["v1"])


# --- Health Check Endpoint ---
@app.get("/health", tags=["Health"])
async def health_check(llm: LLMAdapter = Depends(lambda: llm_adapter_instance)):
    """
    Performs a health check of the service and its dependencies (like LLM adapter).
    """
    # Basic service status
    status = {"status": "ok"}
    http_code = 200

    # Check LLM Adapter health (optional, depends on adapter implementation)
    try:
        llm_healthy = llm.health_check()
        status["llm_adapter_status"] = "ok" if llm_healthy else "degraded"
        if not llm_healthy:
            logger.warning("LLM adapter health check failed.")
            # Decide if this makes the service unhealthy overall
            # status["status"] = "degraded"
            # http_code = 503 # Service Unavailable might be appropriate
    except Exception as e:
        logger.error(f"Health check failed during LLM adapter check: {e}")
        status["llm_adapter_status"] = "error"
        status["status"] = "error"
        http_code = 500  # Internal Server Error

    return JSONResponse(content=status, status_code=http_code)


# --- Entry Point for Uvicorn ---
# You typically run this with `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
# But this block allows running `python -m app.main` for simple cases (less common)
if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Starting Uvicorn server on port {settings.PORT} with reload={settings.RELOAD}"
    )
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=log_level,
    )
