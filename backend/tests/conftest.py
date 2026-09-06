"""Shared fixtures.

Every test runs against its own SQLite file in a temp directory. The app
recreates the database on startup, so tests that share one would be running
against whatever the last one left behind — and `settings` is resolved at
import time, so the path has to be redirected before the app is built.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import create_app


@pytest.fixture
def frontend_dir(tmp_path: Path) -> Path:
    """An empty directory standing in for an unbuilt frontend."""
    directory = tmp_path / "out"
    directory.mkdir()
    return directory


@pytest.fixture
def client(tmp_path: Path, frontend_dir: Path) -> Iterator[TestClient]:
    """A client for an app with a fresh database and no frontend build."""
    settings.database_path = tmp_path / "test.db"
    settings.frontend_dir = frontend_dir
    # Startup refuses to run without one. No test reaches the real model — the
    # chat tests replace `app.llm.completion` — so any non-empty value will do.
    settings.openrouter_api_key = "test-key"
    # `with` runs the lifespan, which is what creates the schema.
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def signed_in(client: TestClient) -> tuple[TestClient, dict[str, str], dict]:
    """A client, auth headers for a signed-in user, and that user's record."""
    response = client.post("/api/auth/login", json={"email": "ada@example.com"})
    body = response.json()
    return client, {"Authorization": f"Bearer {body['token']}"}, body["user"]
