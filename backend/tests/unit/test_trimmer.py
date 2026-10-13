from app.core.schemas import ChatMessage
from app.core.trimmer import trim_messages

# Deterministic stub counter matching the mock engine's heuristic.
count = lambda s: (len(s) + 3) // 4  # noqa: E731


def msg(role, content):
    return ChatMessage(role=role, content=content)


def test_system_preserved_and_oldest_dropped():
    msgs = [
        msg("system", "SYS"),                       # 1 token
        msg("user", "x" * 24),                      # 6 tokens → dropped
        msg("user", "y" * 24),                      # 6 tokens → kept
    ]
    out = trim_messages(msgs, count, budget=10)
    assert [m.content for m in out] == ["SYS", "y" * 24]


def test_fills_budget_with_newest_first():
    msgs = [msg("user", "a" * 8), msg("user", "b" * 8), msg("user", "c" * 8)]  # 2 tok each
    out = trim_messages(msgs, count, budget=5)
    assert [m.content for m in out] == ["b" * 8, "c" * 8]


def test_single_oversized_message_still_kept():
    msgs = [msg("user", "z" * 40)]                  # 10 tokens > budget 5
    out = trim_messages(msgs, count, budget=5)
    assert len(out) == 1 and out[0].content == "z" * 40


def test_huge_system_message_is_never_dropped():
    msgs = [msg("system", "S" * 40), msg("user", "hi")]
    out = trim_messages(msgs, count, budget=2)
    assert out[0].role == "system"
    assert out[-1].content == "hi"


def test_order_preserved():
    msgs = [msg("user", "1"), msg("assistant", "2"), msg("user", "3")]
    out = trim_messages(msgs, count, budget=100)
    assert [m.content for m in out] == ["1", "2", "3"]
