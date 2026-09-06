"""Talking to the model.

Calls `openrouter/openai/gpt-oss-120b` through LiteLLM with Cerebras pinned as
the inference provider, and uses Structured Outputs so a turn comes back as
both something to say and a patch of agreement fields — see `models.ChatTurn`.
"""

import json
import logging

from litellm import completion
from pydantic import ValidationError

from .models import ChatMessage, ChatTurn, MndaFieldsPatch

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

SYSTEM_PROMPT = """\
You are a legal assistant helping someone draft a Common Paper Mutual \
Non-Disclosure Agreement. You are the only interface: there is no form, so \
everything you need must come out of the conversation.

Your job is to find out what belongs on the Cover Page and record it. You can \
see the document being filled in beside you, so the user watches each value \
land as they answer.

How to talk:
- Open by asking what the NDA is for and who the two parties are.
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
- When nothing is left to fill in, say the agreement is ready to download.

What you may record:
- Only what the user actually told you. Never invent a party name, a date, a \
state or a purpose.
- `purpose` is how Confidential Information may be used, written as a phrase \
that completes "for the purpose of ...".
- `effectiveDate` must be `yyyy-mm-dd`. Resolve relative dates like "today" \
or "next Monday" against the current date given below.
- `governingLaw` is a US state, as its name alone: "Delaware", not "Delaware \
law" or "the laws of Delaware".
- `jurisdiction` is a city or county plus a state abbreviation, e.g. "New \
Castle, DE". "courts located in" is added for you, so leave it out.
- `termType` is `expires` when the NDA runs for a fixed number of years, or \
`untilTerminated` when it runs until someone ends it. `termYears` goes with \
`expires`.
- `confidentialityType` is `years` for a fixed protection period or \
`perpetuity` for forever. `confidentialityYears` goes with `years`.
- `modifications` is free text and is genuinely optional. Do not push for it.
- The MNDA term and the term of confidentiality start at the Common Paper \
default of one year. They are not blank, so they will never appear as missing \
— confirm both with the user in your own words before you say the agreement is \
ready.
- Each party needs a print name, a company and a notice address (an email or \
a postal address). A title is optional.

Set a field only on the turn you learn it. Leave everything else unset — the \
values already captured are kept for you, and re-sending them wastes nothing \
but re-sending a wrong one overwrites a right one.\
"""


def _captured(fields: MndaFieldsPatch) -> dict:
    """Only the values the user has actually given.

    A blank field reaches us as an empty string, not as `null` — that is what
    an untouched text input holds, and it is what the client sends. Listing
    those under "Captured so far" tells the model the field is recorded and its
    value is nothing, which contradicts the "Still needed" line below and leaves
    it acknowledging answers without writing them down. So empty values are
    dropped here rather than shown as empty.
    """
    captured: dict = {}
    for key, value in fields.model_dump(by_alias=True, exclude_none=True).items():
        if isinstance(value, dict):
            given = {k: v for k, v in value.items() if v not in (None, "")}
            if given:
                captured[key] = given
        elif value not in (None, ""):
            captured[key] = value
    return captured


def _context(fields: MndaFieldsPatch, missing: list[str], today: str) -> str:
    """The state of the agreement, as a system message before the model's turn.

    Sent every turn rather than once at the start: the values change as the
    conversation goes on, and a stale copy earlier in the history would
    contradict this one.
    """
    captured = _captured(fields)
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
                # Deliberately not "the agreement is ready". The term and the
                # term of confidentiality hold defaults, so they are never
                # missing and may never have been discussed — asserting
                # readiness here would contradict the instruction above to
                # confirm them, and the model would have to pick a side.
                "Every required field is filled. Confirm the MNDA term and the "
                "term of confidentiality with the user if you have not "
                "already, and then say the agreement is ready."
            )
        )
    )


class ModelUnavailable(Exception):
    """The model could not be reached, or answered with something unusable."""


def draft_turn(
    messages: list[ChatMessage],
    fields: MndaFieldsPatch,
    missing: list[str],
    today: str,
) -> ChatTurn:
    """Asks the model for its next turn.

    Raises `ModelUnavailable` for anything that goes wrong, so the router has
    one failure to describe to the user rather than every way LiteLLM, the
    network and the model can each disappoint.
    """
    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": _context(fields, missing, today)},
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
