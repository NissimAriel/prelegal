"""Serving the exported frontend, and coping when it has not been built."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import create_app


@pytest.fixture
def built_frontend(tmp_path: Path) -> Path:
    """A stand-in for the tree `next build` exports."""
    out = tmp_path / "out"
    (out / "mnda").mkdir(parents=True)
    (out / "index.html").write_text("<h1>Sign in</h1>")
    (out / "mnda" / "index.html").write_text("<h1>Mutual NDA</h1>")
    (out / "404.html").write_text("<h1>Not found</h1>")
    return out


@pytest.fixture
def served(tmp_path: Path, built_frontend: Path) -> TestClient:
    settings.database_path = tmp_path / "test.db"
    settings.frontend_dir = built_frontend
    with TestClient(create_app()) as client:
        yield client


def test_root_serves_the_frontend(served: TestClient) -> None:
    response = served.get("/")
    assert response.status_code == 200
    assert "Sign in" in response.text


def test_an_exported_route_is_served(served: TestClient) -> None:
    response = served.get("/mnda/")
    assert response.status_code == 200
    assert "Mutual NDA" in response.text


def test_the_api_is_not_shadowed_by_the_frontend(served: TestClient) -> None:
    """The frontend is mounted at `/`, which matches every path."""
    assert served.get("/api/health").json() == {"status": "ok"}


def test_an_unknown_path_gets_the_exported_404(served: TestClient) -> None:
    response = served.get("/nope")
    assert response.status_code == 404


def test_an_unbuilt_frontend_explains_itself_instead_of_crashing(
    client: TestClient,
) -> None:
    """The backend stays usable without a frontend build; the API still works."""
    response = client.get("/")

    assert response.status_code == 503
    assert "has not been built" in response.text
    assert client.get("/api/health").status_code == 200
