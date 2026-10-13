"""Pydantic models — written for pydantic v1 AND v2 compatibility
(no version-specific APIs), so the device can run pydantic<2."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None          # accepted for OpenAI compatibility; ignored
    messages: List[ChatMessage]
    stream: bool = True
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=640, ge=1, le=1024)
