"""Talking to the model.

Calls `openrouter/openai/gpt-oss-120b` through LiteLLM with Cerebras pinned as
the inference provider, and uses Structured Outputs so a turn comes back as
something to say plus the values it learned — see `models.ChatTurn`.

Nothing here knows about any particular document. The prompt is assembled from
the `DocumentSpec` being drafted and the catalogue of the rest, so a new
document type changes what the model is told without changing this module.
"""

import json
import logging

from litellm import completion
from pydantic import ValidationError

from .documents import SPECS, DocumentSpec, FieldSpec, FieldType
from .models import ChatMessage, ChatTurn, FieldValue

logger = logging.getLogger(__name__)

MODEL = "openrouter/openai/gpt-oss-120b"

#: `order` alone is only a preference: OpenRouter silently falls back to
#: whichever provider it likes, and the fallbacks answered in 30-60s where
#: Cerebras answers in under one. `allow_fallbacks` is what actually pins it,
#: so a Cerebras outage becomes a visible error rather than a slow reply.
EXTRA_BODY = {"provider": {"order": ["cerebras"], "allow_fallbacks": False}}

#: Low is enough to fill in a form from conversation, and keeps replies quick.
REASONING_EFFORT = "low"

#: A turn is a short paragraph plus a small JSON object, so this is generous.
#: It must be set: left unset, OpenRouter reserves the model's entire 40k
#: context up front and rejects the request on a metered account.
MAX_TOKENS = 2000

CONDUCT = """\
You are a legal assistant helping someone draft an agreement from a Common \
Paper template. You are the only interface: there is no form, so everything \
you need must come out of the conversation.

The document is being filled in beside you, so the user watches each value \
land as they answer.

How to talk:
- Ask about one or two things at a time. Never present a list of every \
remaining field.
- End every reply with a question, until there is genuinely nothing left to \
ask. Confirming what you recorded is not a substitute for asking the next \
thing: a reply with no question in it leaves the user staring at a chat that \
looks finished when it is not.
- Keep replies to a short paragraph. No headings, no bullet lists, no markdown.
- When you record something, say briefly what you took from it, so a \
misunderstanding is visible immediately.
- If an answer is ambiguous, ask rather than guess.
- Record only what the user actually told you. Never invent a name, a date, an \
amount or a state, and never copy an example out of a field's description into \
the document.
- Record anything the user told you earlier that you had no field for at the \
time, rather than asking for it a second time.
- Set a value only on the turn you learn it. Leave everything else unset — what \
is already captured is kept for you, and re-sending a wrong value overwrites a \
right one.\
"""

CHOOSING = """\
Choosing the document:
- Match what the user describes against the list above, including the other \
names each document goes by. An abbreviation like "NDA", "SLA", "DPA" or "MSA" \
names a document in that list; treat it as the document it stands for, never \
as something you cannot generate.
- Set `documentType` to the id of the one that fits, and say which you picked \
and why in a sentence.
- The turn you pick a document, pick it and nothing else. You have not been \
shown that document's fields yet, so any value you name is discarded — say \
which document you chose, ask your first question about it, and do not claim \
to have recorded anything. Everything the user has already told you is still \
in front of you and goes in on your next turn.
- Only if nothing in the list does the job: say plainly that you cannot \
generate what they asked for, name the closest document you can generate and \
what it covers instead, and ask whether they want that. Do not pretend a \
different document is the one they asked for, and do not start filling one in \
until they agree.
- If they change their mind later, set `documentType` again. Values already \
captured that the new document also needs are carried over; the rest are \
dropped.\
"""

#: What the model is told before any document has been chosen.
#:
#: The app deliberately holds no document at the start. Naming one here — even
#: as a placeholder — anchors the model to it: told it was "currently drafting a
#: Mutual NDA", it would answer a request for early product access by writing
#: the request into the NDA's purpose field instead of choosing the document
#: that actually fits.
UNCHOSEN = """\
No document has been chosen yet, and choosing one is the only thing to do this \
turn. Work out what the user is trying to achieve, set `documentType` to the \
document that fits, and tell them which you picked and why.

End your reply with a question, so the user has something to answer.

Do not record any values this turn, and do not say that you have. You have not \
been given the chosen document's field list, so anything you name is \
discarded — and a reply claiming a value was recorded when it was not is worse \
than saying nothing. The whole conversation stays in front of you: record what \
the user has already told you on your next turn, without asking again.\
"""


def _catalogue() -> str:
    """Every document, with the other names people call it by.

    The aliases matter: without them the model fails to connect "I need an
    SLA" to a document called "Service Level Agreement" and declines its own
    catalogue.
    """
    lines = []
    for spec in SPECS:
        also = f" Also called: {', '.join(spec.aliases)}." if spec.aliases else ""
        lines.append(f"- {spec.name} (`{spec.id}`): {spec.description}{also}")
    return "\n".join(lines)


def _field_line(field: FieldSpec) -> str:
    """One field, as a single line the model can act on.

    Built as `id (label) — shape. Notes` so every field reads the same way and
    the model is not left inferring which part is which.
    """
    head = f"`{field.id}`"
    if field.label:
        head += f" ({field.label})"

    shape = None
    if field.type is FieldType.CHOICE:
        shape = "one of " + ", ".join(f"`{o.id}`" for o in field.options)
        if field.years_field:
            shape += f", with `{field.years_field}` set to the number of years"
    elif field.type is FieldType.YEARS:
        shape = "a whole number of years, 1 to 99"
    elif field.type is FieldType.DATE:
        shape = "a date"
    if shape:
        head += f" — {shape}"

    # The hint is written for a person reading a form and the guidance for the
    # model; both help, but neither should be repeated back as a second
    # sentence saying the same thing.
    notes = [note.rstrip(".") for note in (field.hint, field.guidance) if note]
    if not field.required:
        # A field holding a default is not optional: it already has a value in
        # the document, it will never be reported missing, and leaving it
        # unmentioned means the user signs a term they never discussed. Saying
        # "do not push for it" here would contradict the standing instruction
        # to confirm defaults.
        if field.default:
            notes.append(
                f"Starts at `{field.default}` — confirm it with the user "
                "rather than assuming it"
            )
        elif not field.guidance:
            # Only a fallback. A field with guidance of its own has already
            # said how it should be treated, and some optional fields do want
            # asking about — an SLA with no uptime target is a strange SLA.
            notes.append("Optional — do not push for it")

    return ". ".join([head, *notes]) + "."


def system_prompt(spec: DocumentSpec | None) -> str:
    """Everything the model needs for this turn.

    With no spec the only task is to choose a document, so the field list is
    omitted entirely — there is nothing yet to fill in.
    """
    if spec is None:
        return "\n\n".join(
            [CONDUCT, f"Documents you can generate:\n{_catalogue()}", CHOOSING, UNCHOSEN]
        )

    fields = "\n".join(
        _field_line(field)
        for field in spec.fields
        # A YEARS field is explained by the choice that consumes it.
        if field.type is not FieldType.YEARS
    )
    return "\n\n".join(
        [
            CONDUCT,
            f"Documents you can generate:\n{_catalogue()}",
            CHOOSING,
            (
                f"You are currently drafting: {spec.name}.\n{spec.description}\n"
                f'In conversation call it "the {spec.short_name}", which is what '
                "the document calls itself."
            ),
            (
                f"The two signatories are called {spec.parties[0]} and "
                f"{spec.parties[1]}. Each needs a print name, a company and a "
                "notice address; a title is optional."
            ),
            f"Values this document needs:\n{fields}",
        ]
    )


def _captured(spec: DocumentSpec | None, values: list[FieldValue]) -> dict[str, str]:
    """Only the values the user has actually given.

    A blank field arrives as an empty string — that is what an untouched input
    holds, and what the client sends. Listing those as captured tells the model
    the field is recorded and its value is nothing, which contradicts the
    "still needed" line below it and leaves the model acknowledging answers
    without writing them down.

    Unknown ids are dropped rather than shown: a stale value left over from a
    previous document type means nothing to this one.
    """
    if spec is None:
        return {}
    return {
        v.id: v.value
        for v in values
        if v.value.strip() and spec.field(v.id) is not None
    }


def _context(
    spec: DocumentSpec | None,
    values: list[FieldValue],
    missing: list[str],
    today: str,
) -> str:
    """The state of the document, as a system message before the model's turn.

    Sent every turn rather than once at the start: the values change as the
    conversation goes on, and a stale copy earlier in the history would
    contradict this one.
    """
    if spec is None:
        return f"Today is {today}."

    captured = _captured(spec, values)
    uncaptured = (
        "\n\nThis document also negotiates terms this app does not capture: "
        + "; ".join(spec.uncaptured)
        + ". If the user raises one, say it is not covered here."
        if spec.uncaptured
        else ""
    )
    return (
        f"Today is {today}.\n\n"
        + (
            f"Captured so far:\n{json.dumps(captured, indent=2)}\n\n"
            if captured
            else "Nothing has been captured yet.\n\n"
        )
        + (
            "Still needed: " + ", ".join(missing) + "."
            if missing
            else (
                # Deliberately not "the document is ready". Fields holding
                # defaults are never missing and may never have been discussed,
                # so asserting readiness here would contradict the instruction
                # to confirm them and the model would have to pick a side.
                "Every required field is filled. Confirm anything you set from "
                "a default rather than from the user, and then say the "
                "document is ready."
            )
        )
        + uncaptured
    )


class ModelUnavailable(Exception):
    """The model could not be reached, or answered with something unusable."""


def draft_turn(
    spec: DocumentSpec | None,
    messages: list[ChatMessage],
    values: list[FieldValue],
    missing: list[str],
    today: str,
) -> ChatTurn:
    """Asks the model for its next turn.

    Raises `ModelUnavailable` for anything that goes wrong, so the router has
    one failure to describe to the user rather than every way LiteLLM, the
    network and the model can each disappoint.
    """
    conversation = [
        {"role": "system", "content": system_prompt(spec)},
        {"role": "system", "content": _context(spec, values, missing, today)},
        *({"role": m.role, "content": m.content} for m in messages),
    ]

    try:
        response = completion(
            model=MODEL,
            messages=conversation,
            response_format=ChatTurn,
            reasoning_effort=REASONING_EFFORT,
            max_tokens=MAX_TOKENS,
            extra_body=EXTRA_BODY,
        )
        content = response.choices[0].message.content
    except Exception as error:
        logger.exception("Model call failed.")
        raise ModelUnavailable(str(error)) from error

    if not content:
        raise ModelUnavailable("The model returned an empty response.")

    try:
        return ChatTurn.model_validate_json(content)
    except ValidationError as error:
        # Structured Outputs should make this impossible, so it means the
        # schema and the model have come apart — worth the full log.
        logger.error("Model response did not match ChatTurn: %s", content)
        raise ModelUnavailable("The model returned an unexpected shape.") from error
