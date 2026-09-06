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


def turn(reply: str = "Got it.", **fields: Any) -> str:
    return json.dumps({"reply": reply, "fields": fields})


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
        json={"messages": [{"role": "user", "content": text}], **body},
    )


def test_a_reply_and_the_fields_it_learned_come_back(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in
    fake_model.content = turn(
        "Noted — a partnership evaluation.",
        purpose="Evaluating a partnership.",
        governingLaw="Delaware",
    )

    response = ask(client, headers, "It's for evaluating a partnership.")

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Noted — a partnership evaluation."
    assert body["fields"]["purpose"] == "Evaluating a partnership."
    assert body["fields"]["governingLaw"] == "Delaware"


def test_fields_the_model_did_not_set_come_back_null(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    """A patch, not a replacement: the client keeps what it already had."""
    client, headers, _ = signed_in
    fake_model.content = turn("Noted.", purpose="Evaluating a partnership.")

    fields = ask(client, headers).json()["fields"]

    assert fields["purpose"] == "Evaluating a partnership."
    assert fields["jurisdiction"] is None
    assert fields["party1"] is None


def test_a_party_is_learned_as_a_nested_object(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in
    fake_model.content = turn(
        "Got it.", party1={"name": "Ada Lovelace", "company": "Acme, Inc."}
    )

    party1 = ask(client, headers).json()["fields"]["party1"]

    assert party1["name"] == "Ada Lovelace"
    assert party1["company"] == "Acme, Inc."
    assert party1["noticeAddress"] is None


def test_the_model_is_told_what_is_captured_and_what_is_missing(
    signed_in: tuple[TestClient, dict[str, str], dict], fake_model: FakeCompletion
) -> None:
    client, headers, _ = signed_in

    ask(
        client,
        headers,
        fields={"purpose": "Evaluating a partnership."},
        missing=["Effective Date", "Governing Law"],
    )

    context = fake_model.conversation[1]["content"]
    assert "Evaluating a partnership." in context
    assert "Effective Date, Governing Law" in context


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
    assert "Confirm the MNDA term" in context


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
