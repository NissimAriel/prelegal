"""Session handling for the stubbed login.

Sessions are real — a random token stored in the database and required by
protected endpoints — while authentication is not: `routers/auth.login` issues
one to anybody who supplies an email address. That split is deliberate. It puts
the token plumbing, the `sessions` table and the `current_user` dependency in
place now, so turning this into a real login is a matter of verifying a
credential before `create_session` is called, not of rewiring the app.
"""

import secrets
import sqlite3

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated

from .db import cursor, utc_now
from .models import User

#: 32 bytes of entropy, url-safe. Not a JWT: nothing needs to read the token's
#: contents, and an opaque token means revoking a session is a DELETE.
TOKEN_BYTES = 32

#: `auto_error=False` so a missing header reaches `current_user`, which raises
#: the same 401 as a bad token. The default would raise 403 instead, which
#: misdescribes an unauthenticated request.
bearer_scheme = HTTPBearer(auto_error=False)


def find_or_create_user(email: str) -> User:
    """Returns the user with this email, creating them on first sight.

    Signing in and signing up are the same action while login is stubbed, so
    there is no "account already exists" case to report.
    """
    with cursor() as db:
        db.execute(
            "INSERT INTO users (email, created_at) VALUES (?, ?)"
            " ON CONFLICT(email) DO NOTHING",
            (email, utc_now()),
        )
        # Re-read rather than using `lastrowid`: on an existing email the insert
        # is a no-op and `lastrowid` would not identify the row we want.
        row = db.execute(
            "SELECT id, email FROM users WHERE email = ?", (email,)
        ).fetchone()
    return User(id=row["id"], email=row["email"])


def create_session(user_id: int) -> str:
    """Issues a session token for a user and returns it."""
    token = secrets.token_urlsafe(TOKEN_BYTES)
    with cursor() as db:
        db.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user_id, utc_now()),
        )
    return token


def delete_session(token: str) -> None:
    """Revokes a session. Silent if the token is already gone."""
    with cursor() as db:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))


def _lookup(token: str) -> sqlite3.Row | None:
    with cursor() as db:
        return db.execute(
            "SELECT users.id, users.email FROM sessions"
            " JOIN users ON users.id = sessions.user_id"
            " WHERE sessions.token = ?",
            (token,),
        ).fetchone()


def current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> User:
    """Resolves the caller from their bearer token, or rejects the request.

    A missing header and an unknown token are the same 401 on purpose: telling
    the two apart would only help someone guessing tokens.
    """
    row = _lookup(credentials.credentials) if credentials else None
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not signed in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(id=row["id"], email=row["email"])


#: The token behind the current request, for endpoints that revoke it.
def current_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> str | None:
    return credentials.credentials if credentials else None
