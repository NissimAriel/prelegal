"""The agreements a user has drafted.

Distinct from `/api/documents`, which is the catalogue of templates the app can
draft: those are the same for everyone, these belong to one person.

Every route takes the user from the session and passes it to the store, which
scopes its queries by it. Nothing here trusts an id on its own.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from .. import documents, drafts
from ..auth import current_user
from ..models import DraftBody, DraftDetail, DraftSummary, User

router = APIRouter(prefix="/drafts", tags=["drafts"])

#: A draft nobody can see is the same as one that is not there. Saying "exists,
#: but not yours" would confirm which ids are real.
NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="No such draft."
)


def _spec(document_type: str):
    spec = documents.get(document_type)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"There is no document type {document_type!r}.",
        )
    return spec


def _values(body: DraftBody) -> dict[str, str]:
    return {value.id: value.value for value in body.values}


@router.get("")
def index(user: Annotated[User, Depends(current_user)]) -> list[DraftSummary]:
    return drafts.list_for(user.id)


@router.post("", status_code=status.HTTP_201_CREATED)
def create(
    body: DraftBody, user: Annotated[User, Depends(current_user)]
) -> DraftSummary:
    return drafts.create(user.id, _spec(body.document_type), _values(body), body.messages)


@router.get("/{draft_id}")
def show(
    draft_id: int, user: Annotated[User, Depends(current_user)]
) -> DraftDetail:
    draft = drafts.get(draft_id, user.id)
    if draft is None:
        raise NOT_FOUND
    return draft


@router.put("/{draft_id}")
def replace(
    draft_id: int, body: DraftBody, user: Annotated[User, Depends(current_user)]
) -> DraftSummary:
    saved = drafts.update(
        draft_id, user.id, _spec(body.document_type), _values(body), body.messages
    )
    if saved is None:
        raise NOT_FOUND
    return saved


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
def destroy(
    draft_id: int, user: Annotated[User, Depends(current_user)]
) -> Response:
    if not drafts.delete(draft_id, user.id):
        raise NOT_FOUND
    return Response(status_code=status.HTTP_204_NO_CONTENT)
