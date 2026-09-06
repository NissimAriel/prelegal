"""Request and response bodies for the API.

Kept in one module because there are few of them and they are shared between
routers; split by resource once that stops being true.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


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


class ChatMessage(BaseModel):
    """One turn of the conversation, in the order it was said."""

    role: Literal["user", "assistant"]
    content: str


class Party(BaseModel):
    """One signatory. Mirrors `Party` in frontend/lib/fields.ts.

    Every field is optional because this is only ever a patch: the model fills
    in what it has just learned and leaves the rest alone.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = None
    title: str | None = None
    company: str | None = None
    notice_address: str | None = None


class MndaFieldsPatch(BaseModel):
    """The fields of a Mutual NDA the model wishes to set this turn.

    Mirrors `MndaFields` in frontend/lib/fields.ts — the names must match, since
    the frontend merges this straight into its own state. Everything is
    optional: omitting a field leaves whatever the user already gave.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    purpose: str | None = None
    #: ISO `yyyy-mm-dd`, the format `<input type="date">` produces.
    effective_date: str | None = None
    term_type: Literal["expires", "untilTerminated"] | None = None
    # Stated as guidance rather than as `ge`/`le` constraints. A strict schema
    # does not enforce numeric bounds, so a validator here would not stop a bad
    # value — it would only turn one into a failed turn, losing the reply along
    # with it. The frontend clamps instead (`clampYears` in lib/fields.ts).
    term_years: int | None = Field(default=None, description="Whole years, 1-99.")
    confidentiality_type: Literal["years", "perpetuity"] | None = None
    confidentiality_years: int | None = Field(
        default=None, description="Whole years, 1-99."
    )
    governing_law: str | None = None
    jurisdiction: str | None = None
    modifications: str | None = None
    party1: Party | None = None
    party2: Party | None = None


class ChatTurn(BaseModel):
    """What the model returns: something to say, and what it learned saying it.

    This is the Structured Output schema, so the docstrings and field names
    here are part of the prompt — the model reads them to decide what goes
    where.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    reply: str = Field(
        description="What to say to the user next. One short paragraph."
    )
    fields: MndaFieldsPatch = Field(
        default_factory=MndaFieldsPatch,
        description="Only the fields learned from the user's latest message.",
    )


class ChatRequest(BaseModel):
    """A turn of conversation, with everything the model needs to answer it.

    The client holds the conversation and the agreement between turns, so the
    server keeps no state of its own — see `routers/chat.py`.
    """

    messages: list[ChatMessage] = Field(
        description="The conversation so far, oldest first."
    )
    fields: MndaFieldsPatch = Field(
        default_factory=MndaFieldsPatch,
        description="Everything captured so far, so the model does not re-ask.",
    )
    missing: list[str] = Field(
        default_factory=list,
        description="Human-readable labels of required fields still blank.",
    )


class ChatResponse(BaseModel):
    """The model's turn, handed back to the client to render and merge."""

    reply: str
    fields: MndaFieldsPatch
