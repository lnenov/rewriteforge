from pydantic import BaseModel, Field, field_validator
from typing import Literal
from app.core.config import settings

# Define allowed styles explicitly
Style = Literal["pirate", "haiku", "formal"]

class RewriteRequest(BaseModel):
    text: str = Field(..., description="The original text to rewrite.")
    style: Style = Field("formal", description="The target style for rewriting.")

    # Custom validator for text length using MAX_TEXT_LENGTH from settings
    @field_validator('text')
    @classmethod
    def text_must_not_exceed_max_length(cls, v: str) -> str:
        max_len = settings.MAX_TEXT_LENGTH
        if len(v) > max_len:
            raise ValueError(f"Input text exceeds maximum length of {max_len} characters.")
        return v

class RewriteResponse(BaseModel):
    original_text: str
    rewritten_text: str
    style: Style
