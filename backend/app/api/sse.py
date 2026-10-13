"""SSE byte framing — the wire contract. Unit-tested byte-for-byte."""
from __future__ import annotations

import json
from typing import Any, Optional

from app import MODEL_NAME


def frame(payload: dict[str, Any]) -> str:
    return "data: " + json.dumps(payload, separators=(",", ":")) + "\n\n"


def done() -> str:
    return "data: [DONE]\n\n"


def error(message: str) -> str:
    return frame({"error": {"message": message}})


def chunk(
    completion_id: str,
    created: int,
    content: Optional[str],
    finish_reason: Optional[str] = None,
) -> str:
    return frame(
        {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": MODEL_NAME,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": content} if content is not None else {},
                    "finish_reason": finish_reason,
                }
            ],
        }
    )
