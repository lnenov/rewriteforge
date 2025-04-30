from typing import Literal

from pydantic import BaseModel, Field

# Define allowed styles explicitly
Style = Literal["pirate", "haiku", "formal"]


class RewriteRequest(BaseModel):
    text: str = Field(..., description="The original text to rewrite.")
    style: Style = Field(
        "formal", description="The target style for rewriting."
    )


class RewriteResponse(BaseModel):
    original_text: str
    rewritten_text: str
    style: Style
