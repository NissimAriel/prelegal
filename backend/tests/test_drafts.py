"""The agreements a user has saved.

This is the first thing in the app where one person's data could reach
another, so most of what follows is about whether it can.
"""

from typing import Any

from fastapi.testclient import TestClient

Headers = dict[str, str]


def body(document_type: str = "mutual-nda", **over: Any) -> dict[str, Any]:
    return {
        "documentType": document_type,
        "values": [{"id": "purpose", "value": "Evaluating a partnership."}],
        "messages": [{"role": "user", "content": "I need an NDA"}],
        **over,
    }


def save(client: TestClient, headers: Headers, **over: Any) -> dict[str, Any]:
    return client.post("/api/drafts", headers=headers, json=body(**over)).json()


class TestOwnership:
    """A draft belongs to one account and is invisible to every other."""

    def test_the_list_shows_only_your_own(
        self, two_users: tuple[TestClient, Headers, Headers]
    ) -> None:
        client, ada, grace = two_users
        save(client, ada)
        save(client, ada)
        save(client, grace)

        assert len(client.get("/api/drafts", headers=ada).json()) == 2
        assert len(client.get("/api/drafts", headers=grace).json()) == 1

    def test_someone_else_s_draft_is_not_found(
        self, two_users: tuple[TestClient, Headers, Headers]
    ) -> None:
        """404, not 403: saying "exists, but not yours" confirms the id is real."""
        client, ada, grace = two_users
        draft = save(client, ada)

        response = client.get(f"/api/drafts/{draft['id']}", headers=grace)

        assert response.status_code == 404

    def test_someone_else_s_draft_cannot_be_overwritten(
        self, two_users: tuple[TestClient, Headers, Headers]
    ) -> None:
        client, ada, grace = two_users
        draft = save(client, ada)

        response = client.put(
            f"/api/drafts/{draft['id']}",
            headers=grace,
            json=body(values=[{"id": "purpose", "value": "Tampered with."}]),
        )

        assert response.status_code == 404
        mine = client.get(f"/api/drafts/{draft['id']}", headers=ada).json()
        assert mine["values"][0]["value"] == "Evaluating a partnership."

    def test_someone_else_s_draft_cannot_be_deleted(
        self, two_users: tuple[TestClient, Headers, Headers]
    ) -> None:
        client, ada, grace = two_users
        draft = save(client, ada)

        assert client.delete(f"/api/drafts/{draft['id']}", headers=grace).status_code == 404
        assert client.get(f"/api/drafts/{draft['id']}", headers=ada).status_code == 200

    def test_drafts_need_a_session(self, client: TestClient) -> None:
        assert client.get("/api/drafts").status_code == 401
        assert client.post("/api/drafts", json=body()).status_code == 401
        assert client.get("/api/drafts/1").status_code == 401
        assert client.put("/api/drafts/1", json=body()).status_code == 401
        assert client.delete("/api/drafts/1").status_code == 401


class TestSaving:
    def test_a_draft_keeps_its_values_and_conversation(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        """The transcript is what lets a reopened draft carry on talking."""
        client, headers, _ = signed_in
        draft = save(client, headers)

        restored = client.get(f"/api/drafts/{draft['id']}", headers=headers).json()

        assert restored["values"] == [
            {"id": "purpose", "value": "Evaluating a partnership."}
        ]
        assert restored["messages"] == [{"role": "user", "content": "I need an NDA"}]

    def test_saving_again_overwrites_rather_than_accumulating(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in
        draft = save(client, headers)

        client.put(
            f"/api/drafts/{draft['id']}",
            headers=headers,
            json=body(values=[{"id": "purpose", "value": "Something else."}]),
        )

        assert len(client.get("/api/drafts", headers=headers).json()) == 1
        restored = client.get(f"/api/drafts/{draft['id']}", headers=headers).json()
        assert restored["values"][0]["value"] == "Something else."

    def test_the_document_type_can_change_as_the_user_changes_their_mind(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in
        draft = save(client, headers)

        client.put(
            f"/api/drafts/{draft['id']}",
            headers=headers,
            json=body("pilot-agreement", values=[]),
        )

        restored = client.get(f"/api/drafts/{draft['id']}", headers=headers).json()
        assert restored["documentType"] == "pilot-agreement"

    def test_an_unknown_document_type_is_rejected(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in

        response = client.post(
            "/api/drafts", headers=headers, json=body("employment-contract")
        )

        assert response.status_code == 422

    def test_a_missing_draft_is_not_found(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in

        assert client.get("/api/drafts/999", headers=headers).status_code == 404
        assert client.put("/api/drafts/999", headers=headers, json=body()).status_code == 404
        assert client.delete("/api/drafts/999", headers=headers).status_code == 404

    def test_deleting_removes_it_from_the_list(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in
        draft = save(client, headers)

        assert client.delete(f"/api/drafts/{draft['id']}", headers=headers).status_code == 204
        assert client.get("/api/drafts", headers=headers).json() == []


class TestTitles:
    """A draft is named by its parties, so a list of them reads as agreements."""

    def test_both_parties_name_the_draft(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in

        draft = save(
            client,
            headers,
            values=[
                {"id": "party1Company", "value": "Acme, Inc."},
                {"id": "party2Company", "value": "Globex"},
            ],
        )

        assert draft["title"] == "Mutual Non-Disclosure Agreement — Acme, Inc. and Globex"

    def test_one_party_is_enough_to_name_it(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in

        draft = save(
            client, headers, values=[{"id": "party1Company", "value": "Acme, Inc."}]
        )

        assert draft["title"] == "Mutual Non-Disclosure Agreement — Acme, Inc."

    def test_with_no_parties_it_is_named_for_the_document(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in

        assert save(client, headers, values=[])["title"] == (
            "Mutual Non-Disclosure Agreement"
        )

    def test_the_title_keeps_up_as_the_parties_are_filled_in(
        self, signed_in: tuple[TestClient, Headers, dict]
    ) -> None:
        client, headers, _ = signed_in
        draft = save(client, headers, values=[])

        saved = client.put(
            f"/api/drafts/{draft['id']}",
            headers=headers,
            json=body(values=[{"id": "party1Company", "value": "Acme, Inc."}]),
        ).json()

        assert saved["title"] == "Mutual Non-Disclosure Agreement — Acme, Inc."
