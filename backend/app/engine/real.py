"""DEVICE-DAY ENGINE — only file aware of llama-cpp-python.

Import is guarded: on GitHub/CI this module is never imported (factory only
reaches it when ENGINE=real). Qwen2.5-instruct recommended sampling defaults
are baked in below."""
from __future__ import annotations

import threading
from typing import Iterator, List

from app.config import Settings
from app.core.schemas import ChatMessage

TOP_P = 0.8
TOP_K = 20
REPEAT_PENALTY = 1.05


def _as_dict(m: ChatMessage) -> dict:
    return m.model_dump() if hasattr(m, "model_dump") else m.dict()


class RealEngine:
    name = "llama-cpp"

    def __init__(self, settings: Settings) -> None:
        try:
            from llama_cpp import Llama  # noqa: PLC0415 — deliberate local import
        except ImportError as exc:
            raise RuntimeError(
                "ENGINE=real requires llama-cpp-python. On the device run:\n"
                "  CMAKE_ARGS='-DGGML_NATIVE=ON' pip install -e './backend[mobile]'"
            ) from exc
        if not settings.model_path.exists():
            raise RuntimeError(f"Model not found: {settings.model_path} (see device runbook)")

        self._lock = threading.Lock()
        self._llm = Llama(
            model_path=str(settings.model_path),
            n_ctx=settings.n_ctx,
            n_threads=settings.n_threads,
            n_threads_batch=settings.n_threads,
            n_batch=settings.n_batch,
            n_gpu_layers=0,       # CPU-only on Android
            use_mmap=True,
            verbose=False,
        )

    def stream(
        self, messages: List[ChatMessage], *, temperature: float, max_tokens: int
    ) -> Iterator[str]:
        with self._lock:  # llama.cpp contexts are not thread-safe
            for c in self._llm.create_chat_completion(
                messages=[_as_dict(m) for m in messages],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=TOP_P,
                top_k=TOP_K,
                repeat_penalty=REPEAT_PENALTY,
                stream=True,
            ):
                piece = c["choices"][0]["delta"].get("content", "")
                if piece:
                    yield piece

    def count_tokens(self, text: str) -> int:
        return len(self._llm.tokenize(text.encode("utf-8", errors="ignore"))) + 6

    def close(self) -> None:
        self._llm = None  # type: ignore[assignment] — drop the model from RAM
