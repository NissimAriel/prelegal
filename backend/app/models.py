"""Request and response bodies for the API.

Kept in one module because there are few of them and they are shared between
routers; split by resource once that stops being true.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from .documents import SPECS


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


class Camel(BaseModel):
    """Serialises as camelCase, which is what the client and the model read.

    The document specs do the same (see `documents.schema.Camel`), so one
    naming convention crosses the API in both directions.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChatMessage(Camel):
    """One turn of the conversation, in the order it was said."""

    role: Literal["user", "assistant"]
    content: str


#: The document types the model may choose from, as an enum so a Structured
#: Output cannot name one that does not exist. Built from the registry so
#: adding a document type needs no change here.
DocumentId = StrEnum(
    "DocumentId", {spec.id.replace("-", "_").upper(): spec.id for spec in SPECS}
)


class FieldValue(Camel):
    """One value, addressed by the field id its spec declares.

    Values travel as a list of id/value pairs rather than as an object with a
    property per field, because the fields differ by document type and a
    Structured Output needs one fixed schema for all of them.
    """

    id: str = Field(description="The field's id, exactly as the spec gives it.")
    value: str = Field(description="The value, as it should appear in the document.")


class ChatTurn(Camel):
    """What the model returns: something to say, and what it learned saying it.

    This is the Structured Output schema, so the field names and descriptions
    here are part of the prompt — the model reads them to decide what goes
    where.
    """

    reply: str = Field(
        description="What to say to the user next. One short paragraph, ending in a question."
    )
    document_type: DocumentId | None = Field(
        default=None,
        description=(
            "Set only when starting or switching to a different document type. "
            "Leave unset to carry on with the current one."
        ),
    )
    values: list[FieldValue] = Field(
        default_factory=list,
        description="Only the fields learned from the user's latest message.",
    )


class ChatRequest(Camel):
    """A turn of conversation, with everything the model needs to answer it.

    The client holds the conversation and the document between turns, so the
    server keeps no state of its own — see `routers/chat.py`.
    """

    messages: list[ChatMessage] = Field(
        description="The conversation so far, oldest first."
    )
    document_type: str | None = Field(
        default=None,
        description="The document being drafted, or null before one is chosen.",
    )
    values: list[FieldValue] = Field(
        default_factory=list,
        description="Everything captured so far, so the model does not re-ask.",
    )
    missing: list[str] = Field(
        default_factory=list,
        description="Labels of required fields still blank.",
    )


class ChatResponse(Camel):
    """The model's turn, handed back to the client to render and merge."""

    reply: str
    #: Always stated, whether or not it changed, so the client never has to
    #: infer which document it is now drafting. Null while the assistant has
    #: still to choose one.
    document_type: str | None
    values: list[FieldValue]
