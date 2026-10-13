qwen-chat — Offline-first AI chat (GitHub-phase build)
ChatGPT-style chat UI + FastAPI backend speaking an OpenAI-compatible SSE contract.The inference engine sits behind a swappable seam: ENGINE=mock (default) replaysrecorded-style fixtures so the entire app is built and tested inside GitHubCodespaces with no model and no mobile hardware. ENGINE=real activatesllama-cpp-python on device day (see docs/runbook-device-day.md).

Quickstart (Codespaces or any laptop)
pip install -e ./backend[dev]python scripts/generate_icons.py        # once; commit the PNGspython -m uvicorn app.main:app --reload --port 8000   # cwd: backend/
Open the forwarded port URL → chat UI running against the mock engine.

Tests
pytest backend/tests                    # unit + contract (e2e deselected by default)pytest backend/tests -m e2e             # Playwright suite (needs: playwright install chromium)ruff check backend scriptspython scripts/export_openapi.py && git diff --exit-code docs/openapi.golden.json

Contract
POST /v1/chat/completions — OpenAI-shaped request, SSE response ofdata: {chunk} frames, final finish_reason: "stop" frame, then data: [DONE].The schema is frozen in docs/openapi.golden.json; CI fails on drift.

Definition of Done (v0.1.0)
 CI green on every PR (lint, unit, contract, e2e, golden schema)
 Streaming, stop, reload-persistence covered by Playwright
 PWA manifest + service worker (cache-first shell, network-only API)
 Tag v0.1.0 + GitHub Release
