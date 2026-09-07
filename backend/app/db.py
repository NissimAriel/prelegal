"""SQLite access.

The database is deliberately disposable: it is deleted and recreated from
`SCHEMA` on every startup (see `main.lifespan`). That is what the V1 foundation
calls for while login is still a stub — it keeps the schema and the code that
reads it from ever drifting apart, and means schema changes need no migration
tooling. It also means nothing a user does survives a restart, which is why no
Docker volume is mounted for it.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from .config import settings

SCHEMA = """
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    -- `scrypt$n$r$p$salt$key`, so the cost parameters travel with the hash and
    -- can be raised later without invalidating existing ones. See `app.auth`.
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);

CREATE TABLE sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL
);

-- One agreement a user is drafting, saved after every turn so nothing is lost
-- to a closed tab. `field_values` and `messages` are JSON: their shape depends
-- on the document type, and nothing queries inside them. Not `values`, which
-- SQLite reserves for INSERT.
CREATE TABLE drafts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    -- Derived from the parties on every write, so the list of drafts reads as
    -- agreements rather than as template names repeated. Stored rather than
    -- computed on read so listing does not have to parse every draft's values.
    title         TEXT NOT NULL,
    field_values  TEXT NOT NULL,
    messages      TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

-- Every query lists one user's drafts, newest first.
CREATE INDEX drafts_by_user ON drafts (user_id, updated_at DESC);
"""


def utc_now() -> str:
    """The current time as an ISO 8601 string, for `created_at` columns."""
    return datetime.now(UTC).isoformat()


def connect() -> sqlite3.Connection:
    """Opens a connection with the settings the rest of the app assumes.

    `Row` gives dict-like access by column name, and foreign keys are off by
    default in SQLite, so `sessions.user_id` would not actually be enforced
    without enabling them on every connection.
    """
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def cursor() -> Iterator[sqlite3.Cursor]:
    """A cursor on a short-lived connection, committing if the body succeeds.

    A connection per request rather than a shared one: SQLite connections are
    not safe to use across threads, and FastAPI runs sync endpoints in a thread
    pool.
    """
    connection = connect()
    try:
        with connection:
            yield connection.cursor()
    finally:
        connection.close()


def reset_database() -> None:
    """Drops any existing database file and recreates the schema."""
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    settings.database_path.unlink(missing_ok=True)
    connection = connect()
    try:
        with connection:
            connection.executescript(SCHEMA)
    finally:
        connection.close()
