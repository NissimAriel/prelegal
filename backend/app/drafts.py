"""Storing the agreements a user is drafting.

A draft is saved after every turn, so closing the tab loses nothing and there
is no Save button to forget. It holds the values captured so far and the
conversation that produced them, which is what lets a reopened draft carry on
talking rather than starting over.

Every query here takes a `user_id` and filters on it. That is deliberate: this
is the first thing in the app where one person's data could reach another, and
scoping in the SQL rather than checking the owner afterwards means a query that
forgets returns nothing rather than everything.
"""

import json
import sqlite3

from .db import cursor, utc_now
from .documents import DocumentSpec
from .models import ChatMessage, DraftDetail, DraftSummary, FieldValue


def _summary(row: sqlite3.Row) -> DraftSummary:
    return DraftSummary(
        id=row["id"],
        document_type=row["document_type"],
        title=row["title"],
        updated_at=row["updated_at"],
    )


def title_for(spec: DocumentSpec, values: dict[str, str]) -> str:
    """Names a draft by its parties, falling back to the document's own name.

    Derived rather than stored so it keeps up as the parties are filled in, and
    derived on the server so every draft in the list is named the same way.
    """
    named = [
        company
        for company in (
            values.get(f"party{index}Company", "").strip() for index in (1, 2)
        )
        if company
    ]
    if len(named) == 2:
        return f"{spec.name} — {named[0]} and {named[1]}"
    if named:
        return f"{spec.name} — {named[0]}"
    return spec.name


def _as_json(values: dict[str, str], messages: list[ChatMessage]) -> tuple[str, str]:
    return (
        json.dumps([{"id": k, "value": v} for k, v in values.items()]),
        json.dumps([m.model_dump() for m in messages]),
    )


def list_for(user_id: int) -> list[DraftSummary]:
    """Every draft this user owns, most recently worked on first."""
    with cursor() as db:
        rows = db.execute(
            "SELECT id, document_type, title, updated_at FROM drafts"
            " WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [_summary(row) for row in rows]


def get(draft_id: int, user_id: int) -> DraftDetail | None:
    """One draft, or None if it does not exist or belongs to somebody else.

    The two cases are deliberately indistinguishable. Reporting "exists, but
    not yours" separately from "no such draft" would confirm which ids are
    real.
    """
    with cursor() as db:
        row = db.execute(
            "SELECT * FROM drafts WHERE id = ? AND user_id = ?",
            (draft_id, user_id),
        ).fetchone()
    if row is None:
        return None
    return DraftDetail(
        id=row["id"],
        document_type=row["document_type"],
        title=row["title"],
        updated_at=row["updated_at"],
        values=[FieldValue(**v) for v in json.loads(row["field_values"])],
        messages=[ChatMessage(**m) for m in json.loads(row["messages"])],
    )


def create(
    user_id: int,
    spec: DocumentSpec,
    values: dict[str, str],
    messages: list[ChatMessage],
) -> DraftSummary:
    now = utc_now()
    stored_values, stored_messages = _as_json(values, messages)
    with cursor() as db:
        db.execute(
            "INSERT INTO drafts"
            " (user_id, document_type, title, field_values, messages, created_at,"
            "  updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                spec.id,
                title_for(spec, values),
                stored_values,
                stored_messages,
                now,
                now,
            ),
        )
        row = db.execute(
            "SELECT id, document_type, title, updated_at FROM drafts"
            " WHERE id = last_insert_rowid()"
        ).fetchone()
    return _summary(row)


def update(
    draft_id: int,
    user_id: int,
    spec: DocumentSpec,
    values: dict[str, str],
    messages: list[ChatMessage],
) -> DraftSummary | None:
    """Overwrites a draft. None if it does not exist or is not this user's."""
    stored_values, stored_messages = _as_json(values, messages)
    with cursor() as db:
        db.execute(
            "UPDATE drafts SET document_type = ?, title = ?, field_values = ?,"
            " messages = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (
                spec.id,
                title_for(spec, values),
                stored_values,
                stored_messages,
                utc_now(),
                draft_id,
                user_id,
            ),
        )
        row = db.execute(
            "SELECT id, document_type, title, updated_at FROM drafts"
            " WHERE id = ? AND user_id = ?",
            (draft_id, user_id),
        ).fetchone()
    return _summary(row) if row else None


def delete(draft_id: int, user_id: int) -> bool:
    """Removes a draft. False if there was nothing of this user's to remove."""
    with cursor() as db:
        removed = db.execute(
            "DELETE FROM drafts WHERE id = ? AND user_id = ?",
            (draft_id, user_id),
        ).rowcount
    return removed > 0
