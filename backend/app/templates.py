"""Reading the curated legal templates.

Everything the app displays as legal text comes from the repo-root `templates/`
directory listed in catalog.json, so that stays the single source of truth and
no wording is duplicated into code.

This used to run in the frontend at build time. It moved here when documents
grew past one: the server already holds the specs, and serving templates on
demand keeps a quarter of a megabyte of contract text out of every page load.
"""

import re
from functools import lru_cache

from .config import REPO_ROOT, settings
from .documents import DocumentSpec

#: Every marker class Common Paper uses to mark a value the parties supply.
#: They differ only in which artifact the value belongs on — Key Terms, an
#: Order Form, a Cover Page, a statement of work, business terms — which
#: matters to a lawyer reading the template but not to us.
MARKER_CLASSES = (
    "keyterms_link",
    "orderform_link",
    "coverpage_link",
    "sow_link",
    "businessterms_link",
)

MARKER_PATTERN = re.compile(
    rf'<span class="(?:{"|".join(MARKER_CLASSES)})">([^<]+)</span>'
)


def templates_dir():
    return settings.templates_dir


@lru_cache(maxsize=32)
def read_template(filename: str) -> str:
    """Reads one markdown template by its filename as listed in catalog.json.

    Cached: templates are read-only files baked into the image, and a long
    agreement is re-read on every page load without it.
    """
    path = (templates_dir() / filename).resolve()
    # The filename comes from a spec, never from a request, but resolving and
    # checking keeps that true if a spec is ever built from user input.
    if not path.is_relative_to(templates_dir().resolve()):
        raise ValueError(f"{filename} is outside the templates directory.")
    return path.read_text(encoding="utf-8")


def markers_in(markdown: str) -> set[str]:
    """Every marked term in a template, in the exact form it is written."""
    return set(MARKER_PATTERN.findall(markdown))


class CoverPageProse:
    """Prose lifted verbatim from a cover page template.

    Only the Mutual NDA has a cover page template. Its preamble and attribution
    are legally load-bearing — the preamble incorporates the Standard Terms by
    reference, and the attribution is what CC BY 4.0 requires — so they are
    taken from the template rather than copied into code where they could fall
    out of step with it.
    """

    def __init__(self, preamble: str, attribution: str):
        self.preamble = preamble
        self.attribution = attribution


def extract_cover_page_prose(markdown: str) -> CoverPageProse:
    """Pulls the preamble and attribution out of a cover page template.

    Raises if either cannot be found, so a template reshaped beyond what this
    understands fails loudly rather than quietly serving an agreement with its
    preamble or licence notice missing.
    """
    lines = markdown.split("\n")

    heading = next(
        (i for i, line in enumerate(lines) if re.match(r"^##\s+USING THIS", line, re.I)),
        None,
    )
    if heading is None:
        raise ValueError('no "## USING THIS …" heading, so the preamble was not found')

    preamble = next((l for l in lines[heading + 1 :] if l.strip()), "")
    if not preamble.startswith("This Mutual Non-Disclosure Agreement"):
        raise ValueError('the paragraph after "USING THIS …" is not the preamble')

    attribution = next((l for l in reversed(lines) if l.strip()), "")
    if not attribution.startswith("Common Paper"):
        raise ValueError("the last line is not the Common Paper attribution")

    return CoverPageProse(preamble, attribution)


#: Printed on every document and shown in the app.
#:
#: Kept here beside the other prose the documents carry, so the wording has one
#: source. It is on the printed page as well as the screen deliberately: the
#: PDF is what leaves the app and reaches a counterparty, and a warning that
#: exists only in the interface is absent from the one artifact that travels.
DRAFT_NOTICE = (
    "This is a draft generated from a template. It has not been reviewed by a "
    "lawyer, and nothing here is legal advice. Have it reviewed by a qualified "
    "lawyer before signing or sending it."
)

#: Attribution for documents with no cover page template of their own, which
#: is every one but the Mutual NDA. CC BY 4.0 requires the credit regardless;
#: catalog.json records the provider and licence this states.
GENERIC_ATTRIBUTION = (
    "Common Paper {name} free to use under "
    "[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)."
)


def prose_for(spec: DocumentSpec) -> CoverPageProse:
    """The preamble and attribution for one document's cover page."""
    if spec.cover_page_template:
        return extract_cover_page_prose(read_template(spec.cover_page_template))
    # No cover page template, so no preamble to incorporate the Standard Terms
    # by reference — writing one would be inventing legal wording. The Standard
    # Terms follow the cover page in full, which serves the same purpose.
    return CoverPageProse("", GENERIC_ATTRIBUTION.format(name=spec.name))
