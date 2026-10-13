"""Environment-driven settings. No hardcoded device assumptions in app code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# backend/app/config.py → repo root
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    # Engine selection: "mock" (default, GitHub/CI) | "real" (device day)
    engine: str = "mock"

    # Mock engine
    mock_delay: float = 0.03                      # seconds between streamed chunks
    mock_fixture_dir: Path = REPO_ROOT / "fixtures"

    # Real engine (device day)
    model_path: Path = REPO_ROOT / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    n_ctx: int = 3072
    n_threads: int = 4
    n_batch: int = 256

    # Shared generation policy
    max_tokens_default: int = 640
    max_tokens_hard: int = 1024
    temperature_default: float = 0.7
    context_reserve: int = 64                     # headroom for chat-template overhead

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            engine=os.environ.get("ENGINE", "mock"),
            mock_delay=float(os.environ.get("MOCK_DELAY", "0.03")),
            mock_fixture_dir=Path(os.environ.get("MOCK_FIXTURE_DIR", REPO_ROOT / "fixtures")),
            model_path=Path(
                os.environ.get(
                    "MODEL_PATH",
                    REPO_ROOT / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf",
                )
            ),
            n_ctx=int(os.environ.get("N_CTX", "3072")),
            n_threads=int(os.environ.get("N_THREADS", "4")),
            n_batch=int(os.environ.get("N_BATCH", "256")),
            max_tokens_default=int(os.environ.get("MAX_TOKENS_DEFAULT", "640")),
            temperature_default=float(os.environ.get("TEMPERATURE", "0.7")),
        )

    @property
    def frontend_dir(self) -> Path:
        """Frontend assets live outside the package; overridable for tests."""
        return Path(os.environ.get("FRONTEND_DIR", REPO_ROOT / "frontend"))
