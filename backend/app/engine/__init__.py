"""Engine factory — the only wiring point that knows concrete engines exist."""
from __future__ import annotations

from app.config import Settings
from app.engine.base import ChatEngine
from app.engine.mock import MockEngine


def build_engine(settings: Settings) -> ChatEngine:
    if settings.engine == "mock":
        return MockEngine(settings.mock_fixture_dir, delay=settings.mock_delay)
    if settings.engine == "real":
        from app.engine.real import RealEngine  # guarded import — device only

        return RealEngine(settings)
    raise ValueError(f"Unknown ENGINE={settings.engine!r} (expected 'mock' or 'real')")


__all__ = ["ChatEngine", "build_engine"]
