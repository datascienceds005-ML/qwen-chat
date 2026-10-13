"""Sliding-window context policy — pure logic, token counter INJECTED.
This makes the most bug-prone component in the system exhaustively testable
in CI (stub counter) while using the real tokenizer on device."""
from __future__ import annotations

from typing import Callable, List

from app.core.schemas import ChatMessage


def trim_messages(
    messages: List[ChatMessage],
    count_tokens: Callable[[str], int],
    *,
    budget: int,
) -> List[ChatMessage]:
    """Keep every system message, then the NEWEST non-system messages whose
    combined cost fits `budget`.

    Rules:
      * System messages are never dropped (caller guarantees they are small).
      * At least one non-system message is always kept, even if oversized —
        the route rejects genuinely impossible requests afterwards.
      * Input order is preserved (oldest → newest).
    """
    system = [m for m in messages if m.role == "system"]
    rest = [m for m in messages if m.role != "system"]

    used = sum(count_tokens(m.content) for m in system)
    kept: List[ChatMessage] = []
    for msg in reversed(rest):
        cost = count_tokens(msg.content)
        if kept and used + cost > budget:
            break
        kept.append(msg)
        used += cost
    kept.reverse()
    return system + kept
