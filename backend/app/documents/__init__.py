"""The registry of document types this app can draft."""

from .schema import (
    ChoiceOption,
    DocumentSpec,
    FieldSpec,
    FieldType,
    SectionSpec,
)
from .specs import SPECS

#: Every spec, by id.
BY_ID: dict[str, DocumentSpec] = {spec.id: spec for spec in SPECS}

#: The document drafted when the user has not said what they want yet. The
#: Mutual NDA is the most commonly wanted and the most completely specified.
DEFAULT_ID = "mutual-nda"


def get(document_id: str) -> DocumentSpec | None:
    return BY_ID.get(document_id)


__all__ = [
    "BY_ID",
    "DEFAULT_ID",
    "ChoiceOption",
    "DocumentSpec",
    "FieldSpec",
    "FieldType",
    "SPECS",
    "SectionSpec",
    "get",
]
