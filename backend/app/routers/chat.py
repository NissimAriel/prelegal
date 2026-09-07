"""The AI chat that fills in the document.

Stateless: the client sends the conversation, which document it is drafting and
everything captured so far, and gets back what to say next plus the values
learned from the latest message.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from .. import documents
from ..auth import current_user
from ..documents import DocumentSpec
from ..llm import ModelUnavailable, draft_turn
from ..models import ChatRequest, ChatResponse, FieldValue, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

#: Enough for a long drafting conversation, short of letting one request carry
#: an unbounded history to a metered API.
MAX_MESSAGES = 100


def _known_values(spec: DocumentSpec, values: list[FieldValue]) -> list[FieldValue]:
    """Drops values the current document has no field for.

    The model is given the field ids and an enum of document types, so a
    mismatch should not happen — but a value written into a document that has
    no place for it would be invisible on screen and unexplainable, so it is
    discarded here and logged.
    """
    kept, unknown = [], []
    for value in values:
        (kept if spec.field(value.id) else unknown).append(value)
    if unknown:
        logger.warning(
            "Model set unknown fields on %s: %s",
            spec.id,
            [v.id for v in unknown],
        )
    return kept


@router.post("")
def chat(
    body: ChatRequest,
    _user: Annotated[User, Depends(current_user)],
) -> ChatResponse:
    """Answers the user's latest message and reports what it learned.

    Requires a session. The conversation is the user's own data, and each turn
    is a billed call to a third party, so neither should be available to an
    anonymous caller.
    """
    if not body.messages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A conversation needs at least one message.",
        )
    if len(body.messages) > MAX_MESSAGES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="This conversation is too long. Start a new document.",
        )

    # No document yet is the normal opening state — the assistant's first job
    # is to choose one. A named document that does not exist is a client bug.
    spec = None
    if body.document_type is not None:
        spec = documents.get(body.document_type)
        if spec is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"There is no document type {body.document_type!r}.",
            )

    try:
        turn = draft_turn(
            spec,
            body.messages,
            body.values,
            body.missing,
            datetime.now(UTC).strftime("%Y-%m-%d"),
        )
    except ModelUnavailable as error:
        # 502, not 500: the failure is upstream, and the client says so.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The assistant is unavailable right now. Please try again.",
        ) from error

    # A switch takes effect immediately, and discards the values named with it.
    #
    # The model is only ever given the current document's field list, so on the
    # turn it picks a different one it is naming fields it has not been shown.
    # It half-manages: it sets a few, misses others, and describes all of them
    # as recorded. Keeping the ones it happened to get right would leave the
    # rest silently missing behind a reply claiming otherwise. Dropping the lot
    # costs a turn — the next one has the field list and the whole conversation
    # still in front of it, so nothing the user said is lost.
    switched = bool(
        turn.document_type and (spec is None or turn.document_type != spec.id)
    )
    if switched:
        spec = documents.get(str(turn.document_type)) or spec

    values: list[FieldValue] = []
    if spec is not None and not switched:
        values = _known_values(spec, turn.values)

    return ChatResponse(
        reply=turn.reply,
        document_type=spec.id if spec else None,
        values=values,
    )
