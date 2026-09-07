"""The AI chat endpoint, with the model replaced.

No test reaches OpenRouter: `app.llm.completion` is monkeypatched throughout,
so the suite runs offline, costs nothing, and does not depend on what a model
happens to say today. What is tested is everything around the call — the
contract, the guards, and how failures surface.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import llm
from app.routers.chat import MAX_MESSAGES


class FakeCompletion:
    """Stands in for `litellm.completion`, recording how it was called."""

    def __init__(self, content: str | None = None, error: Exception | None = None):
        self.content = content
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error:
            raise self.error

        message = type("Message", (), {"content": self.content})
        choice = type("Choice", (), {"message": message})
        return type("Response", (), {"choices": [choice]})

    @property
    def conversation(self) -> list[dict[str, str]]:
        return self.calls[-1]["messages"]


def turn(
    reply: str = "Got it. What next?",
    document_type: str | None = None,
    **values: Any,
) -> str:
    """A model response, in the shape Structured Outputs produces."""
    body: dict[str, Any] = {
        "reply": reply,
        "values": [{"id": k, "value": v} for k, v in values.items()],
    }
    if document_type:
        body["document_type"] = document_type
    return json.dumps(body)


@pytest.fixture
def fake_model(monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeCompletion]:
    fake = FakeCompletion(content=turn())
    monkeypatch.setattr(llm, "completion", fake)
    yield fake


def ask(
    client: TestClient,
    headers: dict[str, str],
    text: str = "Hello",
    **body: Any,
) -> Any:
    return client.post(
        "/api/chat",
        headers=headers,
        json={
            "messages": [{"role": "user", "content": text}],
            "documentType": "mutual-nda",
            **body,
        },
    )


def test_a_reply_and_the_fields_it_learned_come_back(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in
    fake_model.content = turn(
        "Noted — a partnership evaluation. When does it start?",
        purpose="Evaluating a partnership.",
        governingLaw="Delaware",
    )

    response = ask(client, headers, "It's for evaluating a partnership.")

    assert response.status_code == 200
    body = response.json()
    assert body["reply"].startswith("Noted")
    assert body["documentType"] == "mutual-nda"
    assert {v["id"]: v["value"] for v in body["values"]} == {
        "purpose": "Evaluating a partnership.",
        "governingLaw": "Delaware",
    }


def test_only_the_values_the_turn_learned_come_back(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    """A patch, not a replacement: the client keeps what it already had."""
    client, headers, _ = signed_in
    fake_model.content = turn(purpose="Evaluating a partnership.")

    values = ask(client, headers).json()["values"]

    assert [v["id"] for v in values] == ["purpose"]


def test_values_for_fields_this_document_lacks_are_dropped(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    """A value with no field would be invisible on screen and unexplainable."""
    client, headers, _ = signed_in
    fake_model.content = turn(purpose="Evaluating.", targetUptime="99.9%")

    values = ask(client, headers).json()["values"]

    assert [v["id"] for v in values] == ["purpose"]


def test_the_document_type_can_be_switched_mid_conversation(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in
    fake_model.content = turn(
        "That is a Pilot Agreement. How long is the pilot?",
        document_type="pilot-agreement",
    )

    body = ask(client, headers, "Actually I need a pilot").json()

    assert body["documentType"] == "pilot-agreement"


def test_a_switching_turn_records_nothing(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    """The model has not been shown the new document's fields yet.

    Left to name them anyway it half-manages — sets a few, misses others, and
    describes all of them as recorded. Keeping the ones it got right would
    leave the rest silently missing behind a reply claiming otherwise.
    """
    client, headers, _ = signed_in
    fake_model.content = turn(
        "That is a Pilot Agreement. How long is the pilot?",
        document_type="pilot-agreement",
        pilotPeriod="90 days",
        effectiveDate="2026-03-04",
    )

    body = ask(client, headers, "Actually I need a pilot").json()

    assert body["documentType"] == "pilot-agreement"
    assert body["values"] == []


def test_no_document_chosen_is_a_valid_opening_state(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    """The assistant's first job is to work out which document is wanted."""
    client, headers, _ = signed_in
    fake_model.content = turn("What are you trying to do?")

    response = client.post(
        "/api/chat",
        headers=headers,
        json={"messages": [{"role": "user", "content": "I need something drawn up"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["documentType"] is None
    assert body["values"] == []
    # With no document there is no field list to give the model.
    assert "Values this document needs" not in fake_model.conversation[0]["content"]
    assert "No document has been chosen yet" in fake_model.conversation[0]["content"]


def test_an_unknown_document_type_is_rejected(
    client: TestClient, signed_in: tuple[TestClient, dict[str, str], dict]
) -> None:
    client, headers, _ = signed_in

    response = client.post(
        "/api/chat",
        headers=headers,
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "documentType": "employment-contract",
        },
    )

    assert response.status_code == 422


def test_the_model_is_told_what_is_captured_and_what_is_missing(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in

    ask(
        client,
        headers,
        values=[{"id": "purpose", "value": "Evaluating a partnership."}],
        missing=["Effective Date", "Governing Law"],
    )

    context = fake_model.conversation[1]["content"]
    assert "Evaluating a partnership." in context
    assert "Effective Date, Governing Law" in context


def test_blank_fields_are_not_reported_as_captured(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    """An untouched field arrives as "", and must not look like a value.

    Listing it as captured-and-empty contradicts the "Still needed" line in the
    same message, and the model resolves that by acknowledging answers without
    recording them.
    """
    client, headers, _ = signed_in

    ask(
        client,
        headers,
        values=[
            {"id": "purpose", "value": ""},
            {"id": "governingLaw", "value": "Delaware"},
            {"id": "party1Company", "value": "Acme, Inc."},
            {"id": "party1Name", "value": "   "},
        ],
        missing=["Purpose", "Party 1 print name"],
    )

    context = fake_model.conversation[1]["content"]
    assert '"governingLaw": "Delaware"' in context
    assert '"party1Company": "Acme, Inc."' in context
    assert '""' not in context
    assert "party1Name" not in context


def test_an_untouched_agreement_says_so_plainly(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in

    ask(client, headers, values=[], missing=["Purpose"])

    assert "Nothing has been captured yet." in fake_model.conversation[1]["content"]


def test_a_full_agreement_still_asks_for_the_terms_to_be_confirmed(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    """The term fields hold defaults, so they are never reported missing.

    Declaring the agreement ready the moment nothing is missing would let a
    one-year term the user never discussed go out in a signed document.
    """
    client, headers, _ = signed_in

    ask(client, headers, missing=[])

    context = fake_model.conversation[1]["content"]
    assert "Every required field is filled." in context
    assert "Confirm anything you set from a default" in context


def test_the_conversation_reaches_the_model_in_order(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in

    client.post(
        "/api/chat",
        headers=headers,
        json={
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "What is the NDA for?"},
                {"role": "user", "content": "A partnership."},
            ]
        },
    )

    spoken = [m["content"] for m in fake_model.conversation if m["role"] != "system"]
    assert spoken == ["Hello", "What is the NDA for?", "A partnership."]


def test_cerebras_is_the_pinned_provider(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in

    ask(client, headers)

    call = fake_model.calls[-1]
    assert call["model"] == "openrouter/openai/gpt-oss-120b"
    # `allow_fallbacks` is the half that actually pins the provider; without it
    # OpenRouter silently serves the request from somewhere far slower.
    assert call["extra_body"] == {
        "provider": {"order": ["cerebras"], "allow_fallbacks": False}
    }
    assert call["max_tokens"] == 2000


def test_chat_requires_a_session(client: TestClient, fake_model: FakeCompletion) -> None:
    """Each turn is a billed call to a third party, and the user's own data."""
    response = client.post(
        "/api/chat", json={"messages": [{"role": "user", "content": "Hi"}]}
    )

    assert response.status_code == 401
    assert fake_model.calls == []


def test_an_empty_conversation_is_rejected(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in

    response = client.post("/api/chat", headers=headers, json={"messages": []})

    assert response.status_code == 422
    assert fake_model.calls == []


def test_an_overlong_conversation_is_rejected(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in
    messages = [{"role": "user", "content": "Hi"}] * (MAX_MESSAGES + 1)

    response = client.post("/api/chat", headers=headers, json={"messages": messages})

    assert response.status_code == 413
    assert fake_model.calls == []


def test_an_unreachable_model_is_reported_as_a_bad_gateway(
    signed_in: tuple[TestClient, dict[str, str], dict],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Upstream failed, so 502 — not a 500 blaming this service."""
    client, headers, _ = signed_in
    monkeypatch.setattr(llm, "completion", FakeCompletion(error=RuntimeError("boom")))

    response = ask(client, headers)

    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"]


def test_an_unparseable_model_response_is_reported_not_raised(
    signed_in: tuple[TestClient, dict[str, str], dict],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, headers, _ = signed_in
    monkeypatch.setattr(llm, "completion", FakeCompletion(content="not json at all"))

    assert ask(client, headers).status_code == 502


def test_an_empty_model_response_is_reported_not_raised(
    signed_in: tuple[TestClient, dict[str, str], dict],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, headers, _ = signed_in
    monkeypatch.setattr(llm, "completion", FakeCompletion(content=None))

    assert ask(client, headers).status_code == 502
