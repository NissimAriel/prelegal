"""Registering and signing in."""

import sqlite3

from fastapi.testclient import TestClient

from app.config import settings


def user_count() -> int:
    connection = sqlite3.connect(settings.database_path)
    try:
        return connection.execute("SELECT count(*) FROM users").fetchone()[0]
    finally:
        connection.close()


PASSWORD = "correct-horse-battery"


def signup(client: TestClient, email: str = "ada@example.com", **over):
    return client.post(
        "/api/auth/signup", json={"email": email, "password": PASSWORD, **over}
    )


def login(client: TestClient, email: str = "ada@example.com", **over):
    return client.post(
        "/api/auth/login", json={"email": email, "password": PASSWORD, **over}
    )


def test_signing_up_creates_an_account_and_signs_it_in(client: TestClient) -> None:
    response = signup(client)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "ada@example.com"
    assert body["token"]
    assert user_count() == 1


def test_the_password_is_never_stored_as_given(client: TestClient) -> None:
    signup(client)

    connection = sqlite3.connect(settings.database_path)
    try:
        stored = connection.execute("SELECT password_hash FROM users").fetchone()[0]
    finally:
        connection.close()

    assert PASSWORD not in stored
    assert stored.startswith("scrypt$")


def test_an_email_can_only_be_registered_once(client: TestClient) -> None:
    signup(client)

    response = signup(client)

    assert response.status_code == 409
    assert user_count() == 1


def test_capitalisation_does_not_make_a_second_account(client: TestClient) -> None:
    signup(client, "Ada@Example.com")

    assert signup(client, "ada@example.com").status_code == 409
    assert user_count() == 1


def test_a_short_password_is_rejected(client: TestClient) -> None:
    response = signup(client, password="short")

    assert response.status_code == 422
    assert user_count() == 0


def test_a_malformed_email_is_rejected(client: TestClient) -> None:
    assert signup(client, "not-an-email").status_code == 422
    assert user_count() == 0


def test_signing_in_with_the_right_password_works(client: TestClient) -> None:
    created = signup(client).json()

    response = login(client)

    assert response.status_code == 200
    assert response.json()["user"]["id"] == created["user"]["id"]
    # A second sign in is a second session, not a reissue of the first.
    assert response.json()["token"] != created["token"]


def test_signing_in_is_case_insensitive_on_the_email(client: TestClient) -> None:
    signup(client, "ada@example.com")

    assert login(client, "ADA@example.com").status_code == 200


def test_the_wrong_password_is_refused(client: TestClient) -> None:
    signup(client)

    response = login(client, password="not-the-password")

    assert response.status_code == 401


def test_an_unknown_email_is_refused_the_same_way_as_a_wrong_password(
    client: TestClient,
) -> None:
    """Telling them apart would turn sign-in into a way of finding accounts."""
    signup(client, "ada@example.com")

    unknown = login(client, "nobody@example.com")
    wrong = login(client, "ada@example.com", password="not-the-password")

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["detail"] == wrong.json()["detail"]


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
    first = signup(client).json()
    second = login(client).json()

    client.post(
        "/api/auth/logout", headers={"Authorization": f"Bearer {first['token']}"}
    )

    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {second['token']}"}
    ).status_code == 200
