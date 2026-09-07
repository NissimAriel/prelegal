"""Fields that recur across document types.

Several of these documents share whole blocks of terms — every Common Paper
agreement has an effective date and a governing law, and four of them carry an
identical liability-and-claims block. Those are built here so a change to how
one is asked about reaches every document that uses it.

Anything genuinely particular to a single document belongs in its own spec.
"""

from .schema import ChoiceOption, FieldSpec, FieldType, SectionSpec


def effective_date(
    label: str = "Effective date", markers: list[str] | None = None
) -> FieldSpec:
    return FieldSpec(
        id="effectiveDate",
        label=label,
        type=FieldType.DATE,
        required=True,
        markers=markers if markers is not None else ["Effective Date"],
        guidance="`yyyy-mm-dd`. Resolve relative dates against today's date.",
    )


def order_date() -> FieldSpec:
    return FieldSpec(
        id="orderDate",
        label="Order date",
        type=FieldType.DATE,
        required=True,
        markers=["Order Date"],
        guidance="`yyyy-mm-dd`. Resolve relative dates against today's date.",
    )


def governing_law(markers: list[str] | None = None) -> FieldSpec:
    return FieldSpec(
        id="governingLaw",
        label="Governing law",
        hint="US state",
        required=True,
        prefix="Governing Law: ",
        markers=markers if markers is not None else ["Governing Law"],
        guidance=(
            'The state\'s name alone — "Delaware", not "Delaware law" or '
            '"the laws of Delaware".'
        ),
    )


def courts(label: str = "Jurisdiction", markers: list[str] | None = None) -> FieldSpec:
    """Where disputes are heard. Called Jurisdiction or Chosen Courts."""
    return FieldSpec(
        id="jurisdiction",
        label=label,
        hint='City or county and state only — "courts located in" is added for you',
        required=True,
        prefix=f"{label}: courts located in ",
        markers=markers if markers is not None else [label],
        guidance=(
            'A city or county plus a state abbreviation, e.g. "New Castle, DE". '
            'Leave out "courts located in".'
        ),
    )


def law_and_courts_section(title: str) -> SectionSpec:
    """The two share a section, as the Cover Page template lays them out."""
    return SectionSpec(title=title, field_ids=["governingLaw", "jurisdiction"])


def modifications(name: str) -> FieldSpec:
    """Free-text carve-outs from the standard terms. Genuinely optional."""
    return FieldSpec(
        id="modifications",
        label=f"{name} modifications",
        hint="Optional — any changes to the standard terms",
        type=FieldType.LONG_TEXT,
        empty_text="None.",
        guidance="Free text. Genuinely optional — do not push for it.",
    )


def notice_address_field() -> FieldSpec:
    """Where notices go, for documents that mark it as a Key Term.

    Distinct from each signatory's own notice address in the signature block:
    this is the single marked term the prose refers to.
    """
    return FieldSpec(
        id="noticeAddress",
        label="Notice address",
        hint="Where notices under this agreement are sent",
        required=True,
        markers=["Notice Address"],
        guidance="An email or postal address.",
    )


def period(field_id: str, label: str, hint: str, markers: list[str]) -> FieldSpec:
    """A length of time the parties state in their own words."""
    return FieldSpec(
        id=field_id,
        label=label,
        hint=hint,
        required=True,
        markers=markers,
        guidance='A length of time in the user\'s own words, e.g. "12 months".',
    )


def text(
    field_id: str,
    label: str,
    hint: str,
    markers: list[str],
    *,
    required: bool = True,
    long: bool = True,
    empty_text: str | None = None,
    guidance: str | None = None,
) -> FieldSpec:
    """A value the parties describe in prose."""
    return FieldSpec(
        id=field_id,
        label=label,
        hint=hint,
        type=FieldType.LONG_TEXT if long else FieldType.TEXT,
        required=required,
        markers=markers,
        empty_text=empty_text,
        guidance=guidance,
    )


def years_choice(
    field_id: str,
    label: str,
    hint: str,
    options: list[ChoiceOption],
    years_id: str,
    markers: list[str] | None = None,
) -> list[FieldSpec]:
    """A choice whose wording may include a number of years, and that number.

    Returned together because neither is usable alone: the choice's `{years}`
    placeholder has nowhere to read from without the years field, and the years
    field means nothing without the choice that consumes it.
    """
    return [
        FieldSpec(
            id=field_id,
            label=label,
            hint=hint,
            type=FieldType.CHOICE,
            default=options[0].id,
            options=options,
            years_field=years_id,
            markers=markers or [],
        ),
        FieldSpec(id=years_id, type=FieldType.YEARS, default="1"),
    ]


# ---------------------------------------------------------------------------
# The liability and claims block.
#
# The Cloud Service, Software License, Professional Services and Partnership
# Standard Terms all mark the same set of Key Terms around liability, warranties
# and indemnities. Built once here, with the two parties' role names supplied by
# the caller so each document's Covered Claims read the way its own prose does.
# ---------------------------------------------------------------------------


def liability_fields(parties: tuple[str, str]) -> list[FieldSpec]:
    first, second = parties
    return [
        text(
            "generalCapAmount",
            "General cap amount",
            "The general limit on each party's liability",
            ["General Cap Amount"],
            long=False,
            guidance='An amount, e.g. "US$50,000" or "the fees paid in the prior 12 months".',
        ),
        text(
            "increasedCapAmount",
            "Increased cap amount",
            "The higher limit that applies to Increased Claims",
            ["Increased Cap Amount"],
            required=False,
            long=False,
            empty_text="Not applicable.",
            guidance='An amount, or leave blank if there is no increased cap.',
        ),
        text(
            "increasedClaims",
            "Increased claims",
            "Which claims the increased cap applies to",
            ["Increased Claims"],
            required=False,
            empty_text="None.",
        ),
        text(
            "unlimitedClaims",
            "Unlimited claims",
            "Which claims are not capped at all",
            ["Unlimited Claims"],
            required=False,
            empty_text="None.",
        ),
        text(
            "additionalWarranties",
            "Additional warranties",
            "Any warranties beyond the standard terms",
            ["Additional Warranties"],
            required=False,
            empty_text="None.",
        ),
        text(
            "coveredClaims1",
            f"{first} covered claims",
            f"Claims {first} indemnifies against",
            [f"{first} Covered Claim", f"{first} Covered Claims"],
            required=False,
            empty_text="As described in the Standard Terms.",
        ),
        text(
            "coveredClaims2",
            f"{second} covered claims",
            f"Claims {second} indemnifies against",
            [f"{second} Covered Claim", f"{second} Covered Claims"],
            required=False,
            empty_text="As described in the Standard Terms.",
        ),
    ]


def liability_sections(parties: tuple[str, str]) -> list[SectionSpec]:
    first, second = parties
    return [
        SectionSpec(
            title="Liability",
            hint="Caps on what each party can owe the other",
            field_ids=[
                "generalCapAmount",
                "increasedCapAmount",
                "increasedClaims",
                "unlimitedClaims",
            ],
        ),
        SectionSpec(title="Additional Warranties", field_ids=["additionalWarranties"]),
        SectionSpec(
            title="Covered Claims",
            hint="What each party indemnifies the other against",
            field_ids=["coveredClaims1", "coveredClaims2"],
        ),
    ]
