Runbook — Device day (Vivo T3x 5G / Termux)
Preconditions: repo tagged v0.1.0, CI green, all GitHub-phase DoD checked.

Install Termux from F-Droid (NOT Play Store). Settings → Battery → Unrestricted.
Generate SSH key on phone → add as READ-ONLY deploy key on the private repo.
Run scripts/bootstrap-termux.sh (provisions, compiles llama.cpp ONCE, pulls model).
Record real fixtures: python scripts/record_mock.py … → commit to fixtures/.
Smoke test: ENGINE=real python -m uvicorn app.main:app --host 127.0.0.1 --port 8000then curl /v1/chat/completions (stream=false) → OpenAI-shaped JSON.
Chrome → http://localhost:8000 → verify green dot, streaming, stop, reload persistence.
PWA: ⋮ → Install app. Verify airplane-mode launch (shell loads, dot green with engine up).
Funtouch hardening: autostart whitelist Termux, lock in Recents, wake-lock in startscript; ADB one-time fix for the Android 12+ phantom process killer.
Device-validation checklist (record results in docs/):[ ] tokens/sec (Q4_K_M, 4 threads) [ ] 30-min session thermal behavior[ ] RAM headroom (free -h) [ ] survives screen-off (wake lock)[ ] reboot → Termux:Boot autostart [ ] airplane mode full pass
