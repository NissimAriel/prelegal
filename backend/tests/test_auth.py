"""The stubbed login.

These cover the contract the frontend depends on and the behaviour that has to
survive PL-5 replacing the stub with a real credential check.
"""

import sqlite3

from fastapi.testclient import TestClient

from app.config import settings


def user_count() -> int:
    connection = sqlite3.connect(settings.database_path)
    try:
        return connection.execute("SELECT count(*) FROM users").fetchone()[0]
    finally:
        connection.close()


def test_login_creates_a_user_and_returns_a_session(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"email": "ada@example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "ada@example.com"
    assert body["token"]
    assert user_count() == 1


def test_login_accepts_any_email_without_a_password(client: TestClient) -> None:
    """Login is a stub: no credential is required and none is checked."""
    response = client.post("/api/auth/login", json={"email": "nobody@example.com"})
    assert response.status_code == 200


def test_login_rejects_a_malformed_email(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"email": "not-an-email"})

    assert response.status_code == 422
    assert user_count() == 0


def test_signing_in_again_reuses_the_same_user(client: TestClient) -> None:
    first = client.post("/api/auth/login", json={"email": "ada@example.com"})
    second = client.post("/api/auth/login", json={"email": "ada@example.com"})

    assert first.json()["user"]["id"] == second.json()["user"]["id"]
    assert first.json()["token"] != second.json()["token"]
    assert user_count() == 1


def test_email_capitalization_does_not_create_a_second_user(
    client: TestClient,
) -> None:
    first = client.post("/api/auth/login", json={"email": "Ada@Example.com"})
    second = client.post("/api/auth/login", json={"email": "ada@example.com"})

    assert first.json()["user"]["id"] == second.json()["user"]["id"]
    assert first.json()["user"]["email"] == "ada@example.com"
    assert user_count() == 1


def test_me_returns_the_signed_in_user(
    signed_in: tuple[TestClient, dict[str, str], dict],
) -> None:
    client, headers, user = signed_in

    response = client.get("/api/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json() == user


def test_me_rejects_a_request_with_no_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_me_rejects_an_unknown_token(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_logout_revokes_the_session(
    signed_in: tuple[TestClient, dict[str, str], dict],
) -> None:
    client, headers, _ = signed_in

    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_logout_without_a_session_still_succeeds(client: TestClient) -> None:
    """The caller wants to end up signed out, and they already are."""
    assert client.post("/api/auth/logout").status_code == 204


def test_one_session_ending_does_not_end_the_others(client: TestClient) -> None:
    first = client.post("/api/auth/login", json={"email": "ada@example.com"}).json()
    second = client.post("/api/auth/login", json={"email": "ada@example.com"}).json()

    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {first['token']}"})

    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {second['token']}"}
    ).status_code == 200
