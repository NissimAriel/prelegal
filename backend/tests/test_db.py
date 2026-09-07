"""The database is disposable, and that has to stay true."""

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.db import reset_database
from app.main import create_app


def test_reset_discards_existing_data(tmp_path: Path) -> None:
    settings.database_path = tmp_path / "test.db"
    reset_database()
    connection = sqlite3.connect(settings.database_path)
    with connection:
        connection.execute(
            "INSERT INTO users (email, password_hash, created_at)"
            " VALUES ('ada@example.com', 'scrypt$...', 'now')"
        )
    connection.close()

    reset_database()

    connection = sqlite3.connect(settings.database_path)
    try:
        assert connection.execute("SELECT count(*) FROM users").fetchone()[0] == 0
    finally:
        connection.close()


def test_restarting_the_app_wipes_the_database(
    tmp_path: Path, frontend_dir: Path
) -> None:
    settings.database_path = tmp_path / "test.db"
    settings.frontend_dir = frontend_dir

    with TestClient(create_app()) as client:
        client.post(
            "/api/auth/signup",
            json={"email": "ada@example.com", "password": "correct-horse-battery"},
        )

    with TestClient(create_app()) as client:
        connection = sqlite3.connect(settings.database_path)
        try:
            assert connection.execute("SELECT count(*) FROM users").fetchone()[0] == 0
        finally:
            connection.close()


def test_a_session_cannot_outlive_its_user(tmp_path: Path) -> None:
    """Foreign keys are enforced, so `sessions.user_id` is never dangling."""
    settings.database_path = tmp_path / "test.db"
    reset_database()

    connection = sqlite3.connect(settings.database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            try:
                connection.execute(
                    "INSERT INTO sessions (token, user_id, created_at)"
                    " VALUES ('t', 999, 'now')"
                )
            except sqlite3.IntegrityError:
                return
        raise AssertionError("expected a foreign key violation")
    finally:
        connection.close()
