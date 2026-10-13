"""HTTP contract: /api/health + OpenAI-compatible /v1/chat/completions (SSE + sync)."""
from __future__ import annotations

import time
import uuid
from typing import Iterator, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app import APP_VERSION, MODEL_NAME
from app.config import Settings
from app.core.schemas import ChatCompletionRequest, ChatMessage
from app.core.sse import chunk, done, error
from app.core.trimmer import trim_messages

router = APIRouter()


@router.get("/api/health")
def health(request: Request) -> dict:
    return {
        "status": "ok",
        "engine": request.app.state.engine.name,
        "version": APP_VERSION,
    }


def _check_context(
    engine, settings: Settings, trimmed: List[ChatMessage], max_tokens: int
) -> int:
    prompt_tokens = sum(engine.count_tokens(m.content) for m in trimmed)
    prompt_tokens += settings.context_reserve // 2
    if prompt_tokens + max_tokens > settings.n_ctx:
        raise HTTPException(
            400,
            "Conversation too long for the context window. Start a new chat.",
        )
    return prompt_tokens


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest, request: Request) -> object:
    engine = request.app.state.engine
    settings: Settings = request.app.state.settings

    if not body.messages:
        raise HTTPException(400, "messages must not be empty")

    budget = max(64, settings.n_ctx - body.max_tokens - settings.context_reserve)
    trimmed = trim_messages(body.messages, engine.count_tokens, budget=budget)
    prompt_tokens = _check_context(engine, settings, trimmed, body.max_tokens)

    completion_id = "chatcmpl-" + uuid.uuid4().hex[:12]
    created = int(time.time())

    if not body.stream:
        text = "".join(
            engine.stream(trimmed, temperature=body.temperature, max_tokens=body.max_tokens)
        )
        return JSONResponse(
            {
                "id": completion_id,
                "object": "chat.completion",
                "created": created,
                "model": MODEL_NAME,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": engine.count_tokens(text),
                },
            }
        )

    def sse() -> Iterator[str]:
        try:
            for piece in engine.stream(
                trimmed, temperature=body.temperature, max_tokens=body.max_tokens
            ):
                if piece:
                    yield chunk(completion_id, created, piece)
            yield chunk(completion_id, created, None, "stop")
            yield done()
        except Exception as exc:  # surface engine failures to the client
            yield error(str(exc))

    return StreamingResponse(
        sse(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
