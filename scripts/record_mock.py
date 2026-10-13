#!/usr/bin/env python3
"""One-time device run: capture REAL Qwen output into mock fixtures.

    python scripts/record_mock.py --model models/qwen...gguf \
        --triggers code,python --out fixtures/mock_stream.jsonl \
        --prompt "Write a Python greeting function."
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.config import Settings      # noqa: E402
from app.engine.real import RealEngine  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--triggers", default="")
    ap.add_argument("--out", default="fixtures/mock_stream.jsonl")
    ap.add_argument("--id", default=None)
    args = ap.parse_args()

    settings = Settings(engine="real", model_path=Path(args.model))
    engine = RealEngine(settings)
    text = "".join(engine.stream(
        [{"role": "user", "content": args.prompt}],
        temperature=0.7, max_tokens=640,
    ))
    engine.close()

    slug = args.id or re.sub(r"[^a-z0-9]+", "-", args.prompt.lower()).strip("-")[:24]
    record = {"id": slug, "triggers": [t.strip() for t in args.triggers.split(",") if t.strip()],
              "text": text}
    out = REPO / args.out
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(f"appended fixture {slug!r} → {out}")


if __name__ == "__main__":
    main()
