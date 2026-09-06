"""The AI chat that fills in the agreement.

Stateless: the client sends the conversation and everything captured so far,
and gets back what to say next plus the fields learned from the latest message.
Nothing is stored — the database holds users and sessions, not documents.
"""

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import current_user
from ..llm import ModelUnavailable, draft_turn
from ..models import ChatRequest, ChatResponse, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

#: Enough for a long drafting conversation, short of letting one request carry
#: an unbounded history to a metered API.
MAX_MESSAGES = 100


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
            detail="This conversation is too long. Start a new agreement.",
        )

    try:
        turn = draft_turn(
            body.messages,
            body.fields,
            body.missing,
            datetime.now(UTC).strftime("%Y-%m-%d"),
        )
    except ModelUnavailable as error:
        # 502, not 500: the failure is upstream, and the client says so.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The assistant is unavailable right now. Please try again.",
        ) from error

    return ChatResponse(reply=turn.reply, fields=turn.fields)
