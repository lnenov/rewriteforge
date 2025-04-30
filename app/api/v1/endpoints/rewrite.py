import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException

from app.api.v1.models import RewriteRequest, RewriteResponse
from app.core.config import settings
from app.services.rewriter import RewriteService, rewrite_service_instance

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Dependency for Text Length Check (to return 400) ---
# Although Pydantic handles validation (giving 422), the requirement
# specifically asks for 400 on size limit. We can use a dependency.
async def check_text_length(
    request_body: RewriteRequest = Body(
        ...
    ),  # Get raw body access if needed, but Pydantic model is fine
):
    if len(request_body.text) > settings.MAX_TEXT_LENGTH:
        logger.warning(
            f"Rejected request due to excessive length: {len(request_body.text)} chars"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Input text exceeds maximum length of {settings.MAX_TEXT_LENGTH} characters.",
        )
    # Pydantic already validates the style, giving 422 if invalid
    # No need for a separate check here unless 400 is strictly required for style too
    return request_body


# --- Endpoint Definition ---
@router.post(
    "/rewrite",
    response_model=RewriteResponse,
    summary="Rewrite Text",
    description="Rewrites the provided text into the specified style using an LLM.",
    tags=["Rewriting"],  # For grouping in OpenAPI docs
)
async def rewrite_text_endpoint(
    # Use Depends for the length check and get validated body
    request_data: Annotated[RewriteRequest, Depends(check_text_length)],
    # Use Depends for service injection (though singleton instance is also common)
    rewrite_service: RewriteService = Depends(lambda: rewrite_service_instance),
):
    """
    Rewrites text based on the provided style.

    - **text**: The input string (max 5000 characters).
    - **style**: The target style (`pirate`, `haiku`, `formal`). Defaults to `formal`.

    Returns the original text and the rewritten text.
    """
    logger.info(f"Received rewrite request for style: {request_data.style}")

    try:
        rewritten_text = await rewrite_service.rewrite_text(
            text=request_data.text, style=request_data.style
        )
        return RewriteResponse(
            original_text=request_data.text,
            rewritten_text=rewritten_text,
            style=request_data.style,
        )
    except ConnectionError as e:
        logger.error(f"LLM service connection error: {e}")
        raise HTTPException(
            status_code=503, detail="Rewrite service backend is unavailable."
        )
    except ValueError as e:  # Catch specific errors if service raises them
        logger.warning(f"Validation error during rewrite: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception(
            "An unexpected error occurred during text rewriting."
        )  # Logs traceback
        raise HTTPException(
            status_code=500, detail="An internal server error occurred."
        )
