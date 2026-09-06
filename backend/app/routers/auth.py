"""Sign in, identify, and sign out.

Login is a stub — see `app.auth` for what is and is not real about it.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from ..auth import (
    create_session,
    current_token,
    current_user,
    delete_session,
    find_or_create_user,
)
from ..models import LoginRequest, LoginResponse, User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest) -> LoginResponse:
    """Signs a user in by email alone, creating them if they are new.

    No credential is checked. The email is normalized to lower case so that
    signing in twice with different capitalization is one user and one row,
    matching the `COLLATE NOCASE` uniqueness on the column.
    """
    user = find_or_create_user(body.email.lower())
    return LoginResponse(token=create_session(user.id), user=user)


@router.get("/me")
def me(user: Annotated[User, Depends(current_user)]) -> User:
    """The signed-in user. 401 if the token is missing or unknown."""
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: Annotated[str | None, Depends(current_token)]) -> Response:
    """Revokes the caller's session.

    Succeeds even without a valid token: the caller's goal is to end up signed
    out, and they already are.
    """
    if token:
        delete_session(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
