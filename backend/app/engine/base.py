"""Engine protocol. Engines are single-instance and MUST serialize their own
inference (a lock) — the API layer is engine-agnostic."""
from __future__ import annotations

from typing import Iterator, List, Protocol

from app.core.schemas import ChatMessage


class ChatEngine(Protocol):
    name: str

    def stream(
        self,
        messages: List[ChatMessage],
        *,
        temperature: float,
        max_tokens: int,
    ) -> Iterator[str]:
        """Yield text chunks ('tokens') for an assistant reply."""
        ...

    def count_tokens(self, text: str) -> int:
        ...

    def close(self) -> None:
        """Release resources. No-op for the mock engine."""
        ...
