"""Mock engine: replays fixtures recorded from real Qwen-style output
(markdown quirks included) with configurable latency. Adversarially
realistic on purpose — the frontend is tested against THIS, not fantasy text."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Iterator, List

from app.core.schemas import ChatMessage

_TOKEN_RE = re.compile(r"\s+|\S+")

_BUILTIN_DEFAULT = (
    "You said: {message}\n\n"
    "I'm the **mock engine** — the whole app is built and tested in GitHub "
    "with no model required.\n\n"
    "- Streaming works token by token\n"
    "- Stop works mid-stream\n"
    "- History persists across reloads\n\n"
    "Ask me to write *code* to see fenced blocks."
)


def _chunk(text: str) -> List[str]:
    return [m.group(0) for m in _TOKEN_RE.finditer(text)]


class MockEngine:
    name = "mock"

    def __init__(self, fixture_dir: Path, delay: float = 0.03) -> None:
        self._delay = delay
        self._fixtures: List[dict] = []
        fixture_file = fixture_dir / "mock_stream.jsonl"
        if fixture_file.exists():
            for line in fixture_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._fixtures.append(json.loads(line))
        if not any(not fx.get("triggers") for fx in self._fixtures):
            self._fixtures.append({"id": "builtin", "triggers": [], "text": _BUILTIN_DEFAULT})

    # ── fixture selection ────────────────────────────────────────────
    def _select(self, messages: List[ChatMessage]) -> tuple[dict, str]:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        low = last_user.lower()
        for fx in self._fixtures:
            if any(t.lower() in low for t in fx.get("triggers", [])):
                return fx, last_user
        default = next((fx for fx in self._fixtures if not fx.get("triggers")), None)
        return (default or {"text": _BUILTIN_DEFAULT}), last_user

    # ── ChatEngine protocol ──────────────────────────────────────────
    def stream(
        self, messages: List[ChatMessage], *, temperature: float, max_tokens: int
    ) -> Iterator[str]:
        fixture, last_user = self._select(messages)
        text = fixture["text"].replace("{message}", last_user)
        emitted = 0
        for token in _chunk(text):
            if emitted >= max_tokens:
                break
            if self._delay:
                time.sleep(self._delay)
            emitted += 1
            yield token

    def count_tokens(self, text: str) -> int:
        # Deterministic approximation: ~4 chars/token. Good enough for the
        # trimmer policy tests; the real engine uses its own tokenizer.
        return max(1, (len(text) + 3) // 4)

    def close(self) -> None:
        return None
