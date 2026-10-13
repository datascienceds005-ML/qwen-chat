import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "mock_stream.jsonl"


def default_fixture_text(message: str) -> str:
    for line in FIXTURES.read_text(encoding="utf-8").splitlines():
        fx = json.loads(line)
        if not fx.get("triggers"):
            return fx["text"].replace("{message}", message)
    raise AssertionError("no default fixture with empty triggers")


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["engine"] == "mock"


def test_non_streaming_completion_shape(client):
    r = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Ping"}], "stream": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == "qwen2.5-1.5b-instruct"
    choice = body["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["message"]["role"] == "assistant"
    assert choice["message"]["content"] == default_fixture_text("Ping")
    assert body["usage"]["completion_tokens"] > 0


def test_streaming_sse_bytes(client):
    r = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Ping"}], "stream": True},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")

    lines = [ln for ln in r.text.split("\n") if ln.strip()]
    assert lines[-1] == "data: [DONE]"
    for ln in lines[:-1]:
        assert ln.startswith("data: ")

    frames = [json.loads(ln[6:]) for ln in lines[:-1]]
    content = "".join(f["choices"][0]["delta"].get("content") or "" for f in frames)
    assert content == default_fixture_text("Ping")
    assert frames[-1]["choices"][0]["finish_reason"] == "stop"


def test_empty_messages_rejected(client):
    r = client.post("/v1/chat/completions", json={"messages": []})
    assert r.status_code == 400


def test_invalid_role_422(client):
    r = client.post(
        "/v1/chat/completions", json={"messages": [{"role": "wizard", "content": "hi"}]}
    )
    assert r.status_code == 422


def test_context_overflow_400(client):
    huge = "x" * 9000  # mock counter: ~2250 tokens > budget at max_tokens=1024
    r = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": huge}],
            "max_tokens": 1024,
            "stream": False,
        },
    )
    assert r.status_code == 400
    assert "context window" in r.json()["detail"]


def test_frontend_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Qwen" in r.text
