ADR-001 — Inference engine behind an env-selected seam
Status: accepted · Date: v0.1.0

Context
We must build and test the entire product in GitHub Codespaces (x86, no model,no ARM) and later run the identical code on-device (aarch64, llama-cpp-python).

Decision
ChatEngine is a Protocol (stream / count_tokens / close). A factory inapp/engine/__init__.py selects MockEngine or RealEngine from ENGINE.llama-cpp-python lives in the mobile dependency extra and is imported onlyinside engine/real.py. Engines serialize themselves (real engine holds a lock).

Consequences
CI and Codespaces never compile llama.cpp; clone → install → test < 2 min.
The HTTP contract (SSE framing + trimming policy) is engine-independent andfrozen by the golden OpenAPI file + contract tests.
Device day adds zero new architecture: set ENGINE=real, install mobile.
