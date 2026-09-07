"""The document specs, checked against the templates they describe.

The specs are the whole product now — the prompt, the cover page and the
validation are all derived from them — so these tests are less about code than
about whether each spec actually matches its template. The marker coverage test
in particular exists because an earlier audit checked only two of the five
marker classes Common Paper uses and concluded five templates had no fields at
all, when between them they had dozens.
"""

import pytest

from app.documents import SPECS, DocumentSpec
from app.templates import markers_in, prose_for, read_template

#: Markers naming a party rather than a value. The prose says "Customer may
#: ..." the way it says "Provider will ..."; those are the signatories, filled
#: in from the signature block, not fields to ask about.
ROLE_MARKERS = {
    "Customer",
    "Provider",
    "Partner",
    "Company",
    "Controller",
    "Processor",
    "Covered Entity",
    "Business Associate",
    # Cross-references to other agreements, not values this document sets.
    "Agreement",
    "DPA",
}


def is_role(marker: str) -> bool:
    return marker.replace("’", "'").removesuffix("'s") in ROLE_MARKERS


@pytest.mark.parametrize("spec", SPECS, ids=lambda s: s.id)
class TestSpec:
    def test_its_template_exists(self, spec: DocumentSpec) -> None:
        assert read_template(spec.template).strip()

    def test_every_section_names_fields_that_exist(self, spec: DocumentSpec) -> None:
        for section in spec.sections:
            for field_id in section.field_ids:
                assert spec.field(field_id) is not None, (
                    f"section {section.title!r} names unknown field {field_id!r}"
                )

    def test_field_ids_are_unique(self, spec: DocumentSpec) -> None:
        ids = [f.id for f in spec.fields]
        assert len(ids) == len(set(ids)), f"duplicate field ids in {spec.id}"

    def test_no_required_field_has_a_default(self, spec: DocumentSpec) -> None:
        """A pre-filled field is never reported missing, so it is never asked about."""
        for field in spec.fields:
            if field.required:
                assert field.default == "", f"{field.id} is required but pre-filled"

    def test_every_choice_resolves(self, spec: DocumentSpec) -> None:
        for field in spec.fields:
            if field.options:
                assert field.default in {o.id for o in field.options}
                if any("{years}" in o.cover for o in field.options):
                    assert spec.field(field.years_field or "") is not None

    def test_every_marked_value_in_the_template_has_a_field(
        self, spec: DocumentSpec
    ) -> None:
        """Nothing the template asks the parties to supply goes uncollected.

        Every `<span class="..._link">` in the prose is a value someone has to
        fill in. If a spec has no field for one, that term renders as its bare
        label in a document going out for signature.
        """
        claimed = {m for field in spec.fields for m in field.markers}
        marked = {m for m in markers_in(read_template(spec.template)) if not is_role(m)}

        # Possessives refer to the same term as the plain form.
        unclaimed = {
            m
            for m in marked
            if m not in claimed
            and m.replace("’", "'").removesuffix("'s") not in claimed
        }
        assert not unclaimed, f"{spec.id} has no field for: {sorted(unclaimed)}"

    def test_it_has_an_attribution(self, spec: DocumentSpec) -> None:
        """CC BY 4.0 requires the credit, whether or not the template carries one."""
        assert prose_for(spec).attribution.startswith("Common Paper")


def test_every_catalogued_document_has_a_spec() -> None:
    """catalog.json is the product's contents page; nothing may be missing."""
    import json
    from app.config import REPO_ROOT

    catalogue = json.loads((REPO_ROOT / "catalog.json").read_text())
    # The Mutual NDA is catalogued as two files — a cover page and its standard
    # terms — which together make one document.
    filenames = {t["filename"] for t in catalogue["templates"]}
    covered = {s.template for s in SPECS} | {
        s.cover_page_template for s in SPECS if s.cover_page_template
    }
    assert filenames == covered
