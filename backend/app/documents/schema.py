"""How a document type describes itself.

One `DocumentSpec` per template says which values the document needs, how each
should be asked for, and how it renders onto a cover page. Everything else —
the prompt the model is given, the fields the client renders, what counts as
missing, and which template markers get annotated — is derived from these, so
adding a document type means adding a spec rather than writing code.

The specs live on the server because three separate things need them: the
prompt in `app.llm`, the validation of what the model sends back, and the
client's cover page renderer. Keeping them here leaves one copy.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class FieldType(StrEnum):
    """How a value is captured and rendered."""

    #: A short single-line value: a name, a company, a US state.
    TEXT = "text"
    #: Prose that may run to several lines and must keep the breaks it was given.
    LONG_TEXT = "longText"
    #: ISO `yyyy-mm-dd`, rendered as e.g. "March 4, 2026".
    DATE = "date"
    #: One of a fixed set of alternatives, each with its own wording.
    CHOICE = "choice"
    #: A whole number of years, only meaningful alongside a CHOICE that uses it.
    YEARS = "years"


class Camel(BaseModel):
    """Serialises as camelCase, which is what the client reads."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ChoiceOption(Camel):
    """One alternative a `CHOICE` field can take.

    Two wordings, because the same term has to read correctly in two places and
    neither can be derived from the other: `cover` is a complete statement of
    what the parties agreed, `reference` a noun phrase that slots into a
    sentence in the Standard Terms. Both may contain `{years}`, which is
    replaced with the value of the choice's `years_field`.
    """

    id: str
    cover: str
    reference: str


class FieldSpec(Camel):
    """One value a document needs."""

    id: str
    #: Shown above the value on the cover page. Omitted for a field that is
    #: rendered inline inside another field's section.
    label: str | None = None
    #: Smaller explanatory text under the label.
    hint: str | None = None
    type: FieldType = FieldType.TEXT
    #: Whether the document is incomplete without it.
    required: bool = False
    #: Starting value. A required field should not have one — the assistant is
    #: told which required fields are blank and would never ask about a field
    #: that arrived pre-filled.
    default: str = ""
    #: Literal text printed before the value, e.g. "courts located in ".
    prefix: str | None = None
    #: Printed in place of the value when an optional field is left blank.
    empty_text: str | None = None
    #: Told to the model verbatim. Say the format wanted and nothing else.
    guidance: str | None = None
    #: Labels this field supplies in the template's prose, so the Standard
    #: Terms can be annotated with its value. A term is usually marked in more
    #: than one form — "Covered Claim" and "Covered Claims", "Customer" and
    #: "Customer's" — and all of them point at the same value.
    markers: list[str] = Field(default_factory=list)
    options: list[ChoiceOption] = Field(default_factory=list)
    #: For a CHOICE whose wording includes `{years}`, the id of the YEARS field
    #: holding the number.
    years_field: str | None = None


class SectionSpec(Camel):
    """A titled group of fields on the cover page."""

    title: str
    hint: str | None = None
    field_ids: list[str]


class DocumentSpec(Camel):
    """Everything needed to draft one kind of document."""

    #: Stable identifier, matching the template's filename stem.
    id: str
    #: As catalog.json names it.
    name: str
    #: As catalog.json describes it. Shown to the user and given to the model,
    #: which uses it to pick the right document for what they asked for.
    description: str
    #: Filename in `templates/` holding the Standard Terms.
    template: str
    #: Filename of the companion cover page template, where one exists. Only
    #: the Mutual NDA has one.
    cover_page_template: str | None = None
    #: The `<h1>` of the finished document.
    title: str
    #: The sentence above the signature block.
    attest: str
    #: Column headings for the signature block, in order.
    parties: tuple[str, str] = ("Party 1", "Party 2")
    #: What the document is called in running prose, e.g. "MNDA". Used in the
    #: prompt so the assistant speaks about it the way the document does.
    short_name: str
    #: Other names people use for this document, abbreviations included. Given
    #: to the model, which otherwise fails to connect "I need an SLA" to a
    #: document called "Service Level Agreement" and declines its own catalogue.
    aliases: list[str] = Field(default_factory=list)
    #: Every value the document captures, in the order it is asked about. The
    #: per-party fields are appended on construction, so a spec is authored
    #: with only what is particular to it.
    fields: list[FieldSpec] = Field(default_factory=list)
    #: Cover page layout. Fields not named by any section are captured but not
    #: printed as their own section — the party fields, which the signature
    #: block renders.
    sections: list[SectionSpec] = Field(default_factory=list)
    #: Terms the document negotiates that this app does not capture. Shown to
    #: the user, so nobody signs one believing it covered more than it did.
    uncaptured: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _add_party_fields(self) -> "DocumentSpec":
        """Appends the signature block's fields.

        Done here rather than in each spec because every document signs the
        same way, and because `fields` has to hold them by the time the spec is
        serialised — the client renders from that list, and a property would
        not survive the JSON.
        """
        already = {f.id for f in self.fields}
        self.fields += [
            f for f in party_fields(self.parties) if f.id not in already
        ]
        return self

    def field(self, field_id: str) -> FieldSpec | None:
        return next((f for f in self.fields if f.id == field_id), None)


#: What each signatory supplies. Identical across every document, because it is
#: the signature block that needs it and every Common Paper document signs the
#: same way.
PARTY_FIELDS: tuple[tuple[str, str, str | None, bool], ...] = (
    ("Name", "Print name", None, True),
    ("Title", "Title", "Optional", False),
    ("Company", "Company", None, True),
    ("NoticeAddress", "Notice address", "Email or postal address", True),
)


def party_fields(parties: tuple[str, str]) -> list[FieldSpec]:
    """The fields behind the signature block, two parties' worth."""
    return [
        FieldSpec(
            id=f"party{index}{suffix}",
            label=f"{name} {label.lower()}",
            hint=hint,
            required=required,
        )
        for index, name in enumerate(parties, start=1)
        for suffix, label, hint, required in PARTY_FIELDS
    ]
