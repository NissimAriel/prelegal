"""Registering, signing in, and the sessions that follow.

Passwords are hashed with `hashlib.scrypt`, a memory-hard KDF in the standard
library, so there is no dependency to keep patched. The stored form carries its
own cost parameters, which is what makes raising them later possible without
invalidating every existing hash.
"""

import hashlib
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

#: scrypt cost. n=2**14 with r=8 needs ~16 MB and takes ~50-100ms on current
#: hardware — slow enough to make guessing expensive, fast enough that a sign
#: in does not feel broken.
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Hashes a password for storage, salt and cost parameters included.

    The parameters are stored alongside the hash rather than assumed, so a
    later increase does not make existing hashes unverifiable.
    """
    salt = secrets.token_bytes(SALT_BYTES)
    key = hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Checks a password against a stored hash.

    Compared with `compare_digest` so the time taken does not depend on how
    many leading bytes matched. A malformed stored hash is a failure rather
    than an exception: it means the row is unusable, which is not something the
    person signing in can do anything about, and raising here would turn a bad
    row into a 500.
    """
    try:
        scheme, n, r, p, salt_hex, key_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        key = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(key_hex) // 2,
        )
    except (ValueError, TypeError):
        return False
    return secrets.compare_digest(key.hex(), key_hex)


#: Verified against when no user matches the email offered.
#:
#: Without it, signing in with an unregistered address returns in a fraction of
#: the time a registered one takes, and that difference tells anyone who cares
#: to measure it which addresses have accounts.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))

#: `auto_error=False` so a missing header reaches `current_user`, which raises
#: the same 401 as a bad token. The default would raise 403 instead, which
#: misdescribes an unauthenticated request.
bearer_scheme = HTTPBearer(auto_error=False)


class EmailTaken(Exception):
    """Someone has already registered this address."""


def create_user(email: str, password: str) -> User:
    """Registers a new user.

    Raises `EmailTaken` rather than returning the existing user: registering
    an address that already has an account is a different outcome from signing
    in, and conflating them would let anyone claim an existing account.
    """
    with cursor() as db:
        existing = db.execute(
            "SELECT 1 FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            raise EmailTaken(email)
        db.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email, hash_password(password), utc_now()),
        )
        row = db.execute(
            "SELECT id, email FROM users WHERE email = ?", (email,)
        ).fetchone()
    return User(id=row["id"], email=row["email"])


def authenticate(email: str, password: str) -> User | None:
    """Returns the user if the password is right, otherwise None.

    An unknown email is checked against `DUMMY_HASH` so that the work done —
    and therefore the time taken — is the same either way.
    """
    with cursor() as db:
        row = db.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()

    if row is None:
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, row["password_hash"]):
        return None
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
