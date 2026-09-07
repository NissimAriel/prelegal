"""Registering, signing in, identifying, and signing out."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..auth import (
    EmailTaken,
    authenticate,
    create_session,
    create_user,
    current_token,
    current_user,
    delete_session,
)
from ..models import Credentials, LoginResponse, User

router = APIRouter(prefix="/auth", tags=["auth"])


def _signed_in(user: User) -> LoginResponse:
    return LoginResponse(token=create_session(user.id), user=user)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(body: Credentials) -> LoginResponse:
    """Registers a new account and signs it in.

    The email is normalised to lower case so that registering twice with
    different capitalisation is one account, matching the `COLLATE NOCASE`
    uniqueness on the column.
    """
    try:
        user = create_user(body.email.lower(), body.password)
    except EmailTaken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That email already has an account. Sign in instead.",
        ) from None
    return _signed_in(user)


@router.post("/login")
def login(body: Credentials) -> LoginResponse:
    """Signs in an existing account.

    An unknown email and a wrong password give the same answer on purpose:
    telling them apart would turn this endpoint into a way of discovering
    which addresses are registered.
    """
    user = authenticate(body.email.lower(), body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That email and password do not match.",
        )
    return _signed_in(user)


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
