#!/usr/bin/env python3
"""Regenerate docs/openapi.golden.json. CI fails if the contract drifts."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

schema = create_app(Settings(engine="mock", mock_delay=0)).openapi()
out = REPO / "docs" / "openapi.golden.json"
out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {out}")
