from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture()
def client():
    settings = Settings(engine="mock", mock_delay=0.0)
    with TestClient(create_app(settings)) as c:
        yield c
