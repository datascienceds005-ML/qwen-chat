import json

from app.core.sse import chunk, done, error, frame


def test_frame_exact_bytes():
    assert frame({"a": 1}) == 'data: {"a":1}\n\n'


def test_done_exact_bytes():
    assert done() == "data: [DONE]\n\n"


def test_error_shape():
    assert json.loads(error("boom")[6:]) == {"error": {"message": "boom"}}


def test_content_chunk_shape():
    payload = json.loads(chunk("id1", 1700000000, "Hi") [6:])
    assert payload["id"] == "id1"
    assert payload["object"] == "chat.completion.chunk"
    assert payload["choices"][0]["delta"] == {"content": "Hi"}
    assert payload["choices"][0]["finish_reason"] is None


def test_final_chunk_has_empty_delta_and_stop():
    payload = json.loads(chunk("id1", 1700000000, None, "stop")[6:])
    assert payload["choices"][0]["delta"] == {}
    assert payload["choices"][0]["finish_reason"] == "stop"
