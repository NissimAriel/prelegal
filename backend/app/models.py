"""Request and response bodies for the API.

Kept in one module because there are few of them and they are shared between
routers; split by resource once that stops being true.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials for `POST /api/auth/login`.

    There is no password field. Login is a stub for the V1 foundation: any
    valid email address is accepted and identifies a user. Adding real
    authentication means adding the field and a hash check here and in
    `routers/auth.login`, with no change to the client contract's shape.
    """

    email: EmailStr = Field(description="Identifies the user. Never verified.")


class User(BaseModel):
    """A user as the API reports them."""

    id: int
    email: str


class LoginResponse(BaseModel):
    """A newly issued session, returned by `POST /api/auth/login`."""

    token: str = Field(description="Send as `Authorization: Bearer <token>`.")
    user: User
