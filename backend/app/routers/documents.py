"""What documents can be drafted, and what each one needs.

The specs are the single source of truth for a document's fields, and three
things need them: the prompt, the validation of what the model returns, and the
client's cover page renderer. Serving them here means the client renders any
document generically without a second copy of the schemas.
"""

from fastapi import APIRouter, HTTPException, status

from .. import documents
from ..documents import DocumentSpec
from ..models import Camel
from ..templates import DRAFT_NOTICE, prose_for, read_template

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentSummary(Camel):
    """One entry in the catalogue, enough to list and choose from."""

    id: str
    name: str
    description: str


class DocumentDetail(Camel):
    """A document's spec, with the legal text it renders.

    Spec and template travel together because neither is useful alone, and
    fetching them separately would let a client render a spec against the wrong
    template.
    """

    spec: DocumentSpec
    #: Raw markdown of the Standard Terms, rendered verbatim.
    standard_terms: str
    #: The paragraph incorporating the Standard Terms by reference. Empty for
    #: documents with no cover page template of their own.
    preamble: str
    #: The CC BY 4.0 attribution, which the licence requires.
    attribution: str
    #: The warning that this is an unreviewed draft. Served rather than written
    #: into the client so the wording has one source.
    disclaimer: str = DRAFT_NOTICE


@router.get("")
def catalogue() -> list[DocumentSummary]:
    """Every document type, in the order the catalogue lists them."""
    return [
        DocumentSummary(id=spec.id, name=spec.name, description=spec.description)
        for spec in documents.SPECS
    ]


@router.get("/{document_id}")
def detail(document_id: str) -> DocumentDetail:
    """One document's spec and legal text."""
    spec = documents.get(document_id)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"There is no document type {document_id!r}.",
        )
    prose = prose_for(spec)
    return DocumentDetail(
        spec=spec,
        standard_terms=read_template(spec.template),
        preamble=prose.preamble,
        attribution=prose.attribution,
    )
