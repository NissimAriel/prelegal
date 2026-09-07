"""The document types this app can draft.

One spec per document in catalog.json. Names and descriptions follow the
catalogue so the two cannot drift; the fields come from what each template
actually leaves to be filled in.

Templates mark every value their prose refers to with a `<span
class="..._link">Label</span>`, in five flavours — `keyterms_link`,
`orderform_link`, `coverpage_link`, `sow_link` and `businessterms_link` — which
distinguish which artifact the value belongs on but all mean the same thing
here: this is a value the parties supply. Those markers are the authority on
what a document needs, and each field's `markers` name the ones it fills.

Party role markers (Customer, Provider, Partner and their possessives) are not
fields; they are annotated from the signatories' companies instead.
"""

from .common import (
    courts,
    effective_date,
    governing_law,
    law_and_courts_section,
    liability_fields,
    liability_sections,
    modifications,
    notice_address_field,
    order_date,
    period,
    text,
    years_choice,
)
from .schema import ChoiceOption, DocumentSpec, FieldSpec, FieldType, SectionSpec

# ---------------------------------------------------------------------------
# Mutual NDA — the only template with a companion cover page, and so the only
# one whose fields and layout are fully specified by Common Paper.
# ---------------------------------------------------------------------------

MUTUAL_NDA = DocumentSpec(
    id="mutual-nda",
    name="Mutual Non-Disclosure Agreement",
    short_name="MNDA",
    aliases=["NDA", "MNDA", "mutual NDA", "confidentiality agreement", "non-disclosure agreement"],
    description=(
        "A two-way NDA letting each party disclose confidential information for "
        "an agreed purpose, covering permitted use and disclosure, exclusions, "
        "compelled disclosure, return or destruction of information, and remedies."
    ),
    template="mutual-nda.md",
    cover_page_template="mutual-nda-coverpage.md",
    title="Mutual Non-Disclosure Agreement",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this MNDA "
        "as of the Effective Date."
    ),
    fields=[
        FieldSpec(
            id="purpose",
            label="Purpose",
            hint="How Confidential Information may be used",
            type=FieldType.LONG_TEXT,
            required=True,
            markers=["Purpose"],
            guidance=(
                "A phrase completing \"for the purpose of ...\", in the user's "
                "own words. Never substitute a generic purpose for what they "
                "actually said."
            ),
        ),
        effective_date(),
        *years_choice(
            "termType",
            "MNDA term",
            "The length of this MNDA",
            [
                ChoiceOption(
                    id="expires",
                    cover="Expires {years} from the Effective Date.",
                    reference="{years} from the Effective Date",
                ),
                ChoiceOption(
                    id="untilTerminated",
                    cover=(
                        "Continues until terminated in accordance with the terms "
                        "of the MNDA."
                    ),
                    reference=(
                        "period until this MNDA is terminated in accordance with "
                        "its terms"
                    ),
                ),
            ],
            "termYears",
            markers=["MNDA Term"],
        ),
        *years_choice(
            "confidentialityType",
            "Term of confidentiality",
            "How long Confidential Information is protected",
            [
                ChoiceOption(
                    id="years",
                    cover=(
                        "{years} from the Effective Date, but in the case of trade "
                        "secrets until the Confidential Information is no longer "
                        "considered a trade secret under applicable laws."
                    ),
                    reference=(
                        "{years} from the Effective Date, but in the case of trade "
                        "secrets until the Confidential Information is no longer "
                        "considered a trade secret under applicable laws"
                    ),
                ),
                ChoiceOption(
                    id="perpetuity", cover="In perpetuity.", reference="perpetuity"
                ),
            ],
            "confidentialityYears",
            markers=["Term of Confidentiality"],
        ),
        governing_law(),
        courts(),
        modifications("MNDA"),
    ],
    sections=[
        SectionSpec(
            title="Purpose",
            hint="How Confidential Information may be used",
            field_ids=["purpose"],
        ),
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(
            title="MNDA Term", hint="The length of this MNDA", field_ids=["termType"]
        ),
        SectionSpec(
            title="Term of Confidentiality",
            hint="How long Confidential Information is protected",
            field_ids=["confidentialityType"],
        ),
        law_and_courts_section("Governing Law & Jurisdiction"),
        SectionSpec(title="MNDA Modifications", field_ids=["modifications"]),
    ],
)


# ---------------------------------------------------------------------------
# Subscription products: a Cover Page carrying Key Terms and an Order Form.
# ---------------------------------------------------------------------------

CLOUD_SERVICE = DocumentSpec(
    id="cloud-service-agreement",
    name="Cloud Service Agreement",
    short_name="Agreement",
    aliases=["CSA", "SaaS agreement", "subscription agreement", "terms of service"],
    description=(
        "Standard SaaS agreement for selling access to a hosted cloud service, "
        "covering access and use rights, customer data, fees and payment, "
        "warranties, indemnification, limitation of liability, and term and "
        "termination."
    ),
    template="cloud-service-agreement.md",
    title="Cloud Service Agreement — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this "
        "Agreement as of the Effective Date."
    ),
    parties=("Customer", "Provider"),
    fields=[
        effective_date(),
        order_date(),
        period(
            "subscriptionPeriod",
            "Subscription period",
            "How long each subscription runs",
            ["Subscription Period", "Subscription Periods"],
        ),
        text(
            "useLimitations",
            "Use limitations",
            "Seats, volume or other caps on use",
            ["Use Limitations"],
        ),
        text(
            "technicalSupport",
            "Technical support",
            "What support the provider commits to",
            ["Technical Support"],
        ),
        text(
            "paymentProcess",
            "Payment process",
            "Fees, invoicing and payment terms",
            ["Payment Process"],
        ),
        period(
            "nonRenewalNoticeDate",
            "Non-renewal notice",
            "How much notice is needed to stop a renewal",
            ["Non-Renewal Notice Date"],
        ),
        governing_law(),
        courts("Chosen courts", ["Chosen Courts"]),
        *liability_fields(("Customer", "Provider")),
        modifications("Agreement"),
    ],
    sections=[
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(title="Order Date", field_ids=["orderDate"]),
        SectionSpec(title="Subscription Period", field_ids=["subscriptionPeriod"]),
        SectionSpec(title="Use Limitations", field_ids=["useLimitations"]),
        SectionSpec(title="Technical Support", field_ids=["technicalSupport"]),
        SectionSpec(title="Payment Process", field_ids=["paymentProcess"]),
        SectionSpec(
            title="Non-Renewal Notice Date", field_ids=["nonRenewalNoticeDate"]
        ),
        law_and_courts_section("Governing Law & Chosen Courts"),
        *liability_sections(("Customer", "Provider")),
        SectionSpec(title="Agreement Modifications", field_ids=["modifications"]),
    ],
    uncaptured=["Any Data Processing Agreement referenced by these terms"],
)

SOFTWARE_LICENSE = DocumentSpec(
    id="software-license-agreement",
    name="Software License Agreement",
    short_name="Agreement",
    aliases=["EULA", "licence agreement", "on-premise licence", "self-hosted licence"],
    description=(
        "License agreement for on-premise or self-hosted software, granting a "
        "limited non-exclusive license for a subscription period and covering "
        "usage restrictions, delivery, support, audit rights, and warranties."
    ),
    template="software-license-agreement.md",
    title="Software License Agreement — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this "
        "Agreement as of the Effective Date."
    ),
    parties=("Customer", "Provider"),
    fields=[
        effective_date(),
        order_date(),
        period(
            "subscriptionPeriod",
            "Subscription period",
            "How long each licence period runs",
            ["Subscription Period", "Subscription Periods"],
        ),
        text(
            "permittedUses",
            "Permitted uses",
            "What the software may be used for",
            ["Permitted Uses"],
        ),
        text(
            "licenseLimits",
            "License limits",
            "Seats, installations, cores or other caps",
            ["License Limits"],
        ),
        text(
            "paymentProcess",
            "Payment process",
            "Fees, invoicing and payment terms",
            ["Payment Process"],
        ),
        period(
            "warrantyPeriod",
            "Warranty period",
            "How long the software warranty lasts",
            ["Warranty Period"],
        ),
        period(
            "nonRenewalNoticeDate",
            "Non-renewal notice",
            "How much notice is needed to stop a renewal",
            ["Non-Renewal Notice Date"],
        ),
        text(
            "deletionProcedure",
            "Deletion procedure",
            "What happens to the software when the licence ends",
            ["Deletion Procedure"],
            required=False,
            empty_text="As described in the Standard Terms.",
        ),
        governing_law(),
        courts("Chosen courts", ["Chosen Courts"]),
        *liability_fields(("Customer", "Provider")),
        modifications("Agreement"),
    ],
    sections=[
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(title="Order Date", field_ids=["orderDate"]),
        SectionSpec(title="Subscription Period", field_ids=["subscriptionPeriod"]),
        SectionSpec(title="Permitted Uses", field_ids=["permittedUses"]),
        SectionSpec(title="License Limits", field_ids=["licenseLimits"]),
        SectionSpec(title="Payment Process", field_ids=["paymentProcess"]),
        SectionSpec(title="Warranty Period", field_ids=["warrantyPeriod"]),
        SectionSpec(
            title="Non-Renewal Notice Date", field_ids=["nonRenewalNoticeDate"]
        ),
        SectionSpec(title="Deletion Procedure", field_ids=["deletionProcedure"]),
        law_and_courts_section("Governing Law & Chosen Courts"),
        *liability_sections(("Customer", "Provider")),
        SectionSpec(title="Agreement Modifications", field_ids=["modifications"]),
    ],
)

SERVICE_LEVEL = DocumentSpec(
    id="service-level-agreement",
    name="Service Level Agreement",
    short_name="SLA",
    aliases=["SLA", "uptime agreement", "service levels"],
    description=(
        "Defines target uptime for a cloud service, how uptime is calculated, "
        "excluded downtime, support response commitments, and service credits "
        "as the remedy for missed targets."
    ),
    template="service-level-agreement.md",
    title="Service Level Agreement — Cover Page",
    attest="By signing this Cover Page, each party agrees to enter into this SLA.",
    parties=("Customer", "Provider"),
    fields=[
        text(
            "targetUptime",
            "Target uptime",
            "The uptime percentage committed to",
            ["Target Uptime"],
            long=False,
            guidance='A percentage, e.g. "99.9%".',
        ),
        period(
            "subscriptionPeriod",
            "Subscription period",
            "The period uptime is measured over",
            ["Subscription Period"],
        ),
        text(
            "uptimeCredit",
            "Uptime credit",
            "The credit owed when uptime is missed",
            ["Uptime Credit"],
        ),
        text(
            "supportChannel",
            "Support channel",
            "How the customer raises support requests",
            ["Support Channel"],
            long=False,
        ),
        text(
            "targetResponseTime",
            "Target response time",
            "How quickly support responds",
            ["Target Response Time"],
            long=False,
        ),
        text(
            "responseTimeCredit",
            "Response time credit",
            "The credit owed when response times are missed",
            ["Response Time Credit"],
        ),
        text(
            "scheduledDowntime",
            "Scheduled downtime",
            "Maintenance windows excluded from uptime",
            ["Scheduled Downtime"],
            required=False,
            empty_text="None.",
        ),
    ],
    sections=[
        SectionSpec(title="Target Uptime", field_ids=["targetUptime"]),
        SectionSpec(title="Subscription Period", field_ids=["subscriptionPeriod"]),
        SectionSpec(title="Uptime Credit", field_ids=["uptimeCredit"]),
        SectionSpec(title="Support Channel", field_ids=["supportChannel"]),
        SectionSpec(title="Target Response Time", field_ids=["targetResponseTime"]),
        SectionSpec(title="Response Time Credit", field_ids=["responseTimeCredit"]),
        SectionSpec(title="Scheduled Downtime", field_ids=["scheduledDowntime"]),
    ],
    uncaptured=["The Cloud Service Agreement this SLA attaches to"],
)

PILOT = DocumentSpec(
    id="pilot-agreement",
    name="Pilot Agreement",
    short_name="Agreement",
    aliases=["proof of concept", "POC", "trial agreement", "evaluation agreement"],
    description=(
        "Short-term paid or unpaid pilot granting a customer access to a product "
        "for defined evaluation purposes during a pilot period, with conversion, "
        "feedback, confidentiality, and end-of-pilot terms."
    ),
    template="pilot-agreement.md",
    title="Pilot Agreement — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this "
        "Agreement as of the Effective Date."
    ),
    parties=("Customer", "Provider"),
    fields=[
        effective_date(),
        period(
            "pilotPeriod", "Pilot period", "How long the pilot runs", ["Pilot Period"]
        ),
        text(
            "generalCapAmount",
            "General cap amount",
            "The general limit on each party's liability",
            ["General Cap Amount"],
            long=False,
            guidance='An amount, e.g. "US$50,000" or "the fees paid".',
        ),
        notice_address_field(),
        governing_law(),
        courts("Chosen courts", ["Chosen Courts"]),
        modifications("Agreement"),
    ],
    sections=[
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(title="Pilot Period", field_ids=["pilotPeriod"]),
        SectionSpec(title="General Cap Amount", field_ids=["generalCapAmount"]),
        SectionSpec(title="Notice Address", field_ids=["noticeAddress"]),
        law_and_courts_section("Governing Law & Chosen Courts"),
        SectionSpec(title="Agreement Modifications", field_ids=["modifications"]),
    ],
)

AI_ADDENDUM = DocumentSpec(
    id="ai-addendum",
    name="AI Addendum",
    short_name="Addendum",
    aliases=["AI terms", "AI addendum", "machine learning addendum", "LLM terms"],
    description=(
        "Layers AI-specific terms onto an existing product agreement, covering "
        "permitted use of AI services, ownership and handling of Input and "
        "Output, model training restrictions, and AI-related warranties and "
        "disclaimers."
    ),
    template="ai-addendum.md",
    title="AI Addendum — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this "
        "Addendum as of the Effective Date."
    ),
    parties=("Customer", "Provider"),
    fields=[
        effective_date(markers=[]),
        text(
            "trainingData",
            "Training data",
            "What data may be used to train models",
            ["Training Data"],
        ),
        text(
            "trainingPurposes",
            "Training purposes",
            "What that training may be for",
            ["Training Purposes"],
        ),
        text(
            "trainingRestrictions",
            "Training restrictions",
            "Limits on training",
            ["Training Restrictions"],
            required=False,
            empty_text="None.",
        ),
        text(
            "improvementRestrictions",
            "Improvement restrictions",
            "Limits on using data to improve the product",
            ["Improvement Restrictions"],
            required=False,
            empty_text="None.",
        ),
        modifications("Addendum"),
    ],
    sections=[
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(title="Training Data", field_ids=["trainingData"]),
        SectionSpec(title="Training Purposes", field_ids=["trainingPurposes"]),
        SectionSpec(
            title="Training Restrictions", field_ids=["trainingRestrictions"]
        ),
        SectionSpec(
            title="Improvement Restrictions", field_ids=["improvementRestrictions"]
        ),
        SectionSpec(title="Addendum Modifications", field_ids=["modifications"]),
    ],
    uncaptured=["The product agreement this addendum attaches to"],
)

# ---------------------------------------------------------------------------
# The remaining documents. Each one's fields come from the Key Terms, Business
# Terms and SOW values its own template marks up.
# ---------------------------------------------------------------------------

BUSINESS_ASSOCIATE = DocumentSpec(
    id="business-associate-agreement",
    name="Business Associate Agreement",
    short_name="BAA",
    aliases=["BAA", "HIPAA agreement", "PHI agreement"],
    description=(
        "HIPAA Business Associate Agreement governing a provider's use and "
        "disclosure of Protected Health Information on behalf of a covered "
        "entity, including safeguards, subcontractor flow-down, breach "
        "notification, and termination duties."
    ),
    template="business-associate-agreement.md",
    title="Business Associate Agreement — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this BAA "
        "as of the BAA Effective Date."
    ),
    parties=("Company", "Provider"),
    fields=[
        effective_date("BAA effective date", markers=["BAA Effective Date"]),
        period(
            "breachNotificationPeriod",
            "Breach notification period",
            "How quickly a breach must be reported",
            ["Breach Notification Period"],
        ),
        text(
            "limitations",
            "Limitations",
            "Limits on how Protected Health Information may be used or disclosed",
            ["Limitations"],
            required=False,
            empty_text="None beyond the Standard Terms.",
        ),
        modifications("BAA"),
    ],
    sections=[
        SectionSpec(title="BAA Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(
            title="Breach Notification Period", field_ids=["breachNotificationPeriod"]
        ),
        SectionSpec(title="Limitations", field_ids=["limitations"]),
        SectionSpec(title="BAA Modifications", field_ids=["modifications"]),
    ],
    uncaptured=["The underlying agreement this BAA attaches to"],
)

DATA_PROCESSING = DocumentSpec(
    id="data-processing-agreement",
    name="Data Processing Agreement",
    short_name="DPA",
    aliases=["DPA", "GDPR agreement", "data processing addendum"],
    description=(
        "GDPR/CCPA-oriented agreement setting out the controller, processor and "
        "subprocessor relationships, processing instructions, security measures, "
        "international transfer mechanisms, and audit and deletion obligations."
    ),
    template="data-processing-agreement.md",
    title="Data Processing Agreement — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this DPA "
        "as of the Effective Date."
    ),
    parties=("Customer", "Provider"),
    fields=[
        effective_date(markers=[]),
        text(
            "natureAndPurpose",
            "Nature and purpose of processing",
            "What the processor does with the data, and why",
            ["Nature and Purpose of Processing"],
        ),
        text(
            "categoriesOfPersonalData",
            "Categories of personal data",
            "What kinds of personal data are processed",
            ["Categories of Personal Data"],
        ),
        text(
            "categoriesOfDataSubjects",
            "Categories of data subjects",
            "Whose personal data is processed",
            ["Categories of Data Subjects"],
        ),
        period(
            "durationOfProcessing",
            "Duration of processing",
            "How long the processing continues",
            ["Duration of Processing"],
        ),
        text(
            "frequencyOfTransfer",
            "Frequency of transfer",
            "How often data is transferred",
            ["Frequency of Transfer"],
            long=False,
            guidance='e.g. "continuous" or "monthly".',
        ),
        text(
            "specialCategoryData",
            "Special category data",
            "Any sensitive data processed",
            ["Special Category Data"],
            required=False,
            empty_text="None.",
        ),
        text(
            "specialCategorySafeguards",
            "Special category safeguards",
            "Extra restrictions or safeguards for sensitive data",
            ["Special Category Data Restrictions or Safeguards"],
            required=False,
            empty_text="Not applicable.",
        ),
        text(
            "approvedSubprocessors",
            "Approved subprocessors",
            "Who else may process the data",
            ["Approved Subprocessors"],
            required=False,
            empty_text="None.",
        ),
        text(
            "securityPolicy",
            "Security policy",
            "The technical and organisational measures in place",
            ["Security Policy"],
        ),
        text(
            "providerSecurityContact",
            "Provider security contact",
            "Who to notify about security matters",
            ["Provider Security Contact"],
            long=False,
            guidance="An email address.",
        ),
        text(
            "governingMemberState",
            "Governing member state",
            "The EEA member state whose law governs, where applicable",
            ["Governing Member State"],
            required=False,
            long=False,
            empty_text="Not applicable.",
        ),
        modifications("DPA"),
    ],
    sections=[
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(
            title="Nature and Purpose of Processing", field_ids=["natureAndPurpose"]
        ),
        SectionSpec(
            title="Categories of Personal Data",
            field_ids=["categoriesOfPersonalData"],
        ),
        SectionSpec(
            title="Categories of Data Subjects",
            field_ids=["categoriesOfDataSubjects"],
        ),
        SectionSpec(
            title="Duration of Processing", field_ids=["durationOfProcessing"]
        ),
        SectionSpec(title="Frequency of Transfer", field_ids=["frequencyOfTransfer"]),
        SectionSpec(
            title="Special Category Data",
            field_ids=["specialCategoryData", "specialCategorySafeguards"],
        ),
        SectionSpec(
            title="Approved Subprocessors", field_ids=["approvedSubprocessors"]
        ),
        SectionSpec(
            title="Security",
            field_ids=["securityPolicy", "providerSecurityContact"],
        ),
        SectionSpec(
            title="Governing Member State", field_ids=["governingMemberState"]
        ),
        SectionSpec(title="DPA Modifications", field_ids=["modifications"]),
    ],
    uncaptured=["The underlying agreement this DPA attaches to"],
)

DESIGN_PARTNER = DocumentSpec(
    id="design-partner-agreement",
    name="Design Partner Agreement",
    short_name="Agreement",
    aliases=["early access agreement", "beta agreement", "design partnership", "pre-release access"],
    description=(
        "For early-access design partnerships, giving a partner pre-release "
        "product access in exchange for feedback and programme participation, "
        "and addressing feedback ownership, confidentiality, and publicity "
        "rights."
    ),
    template="design-partner-agreement.md",
    title="Design Partner Agreement — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this "
        "Agreement as of the Effective Date."
    ),
    parties=("Partner", "Provider"),
    fields=[
        effective_date(),
        text(
            "program",
            "Program",
            "What the design partner programme involves",
            ["Program"],
        ),
        period("term", "Term", "How long the programme runs", ["Term"]),
        text(
            "fees",
            "Fees",
            "What the partner pays, if anything",
            ["Fees"],
            required=False,
            empty_text="None.",
        ),
        notice_address_field(),
        governing_law(),
        courts("Chosen courts", ["Chosen Courts"]),
        modifications("Agreement"),
    ],
    sections=[
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(title="Program", field_ids=["program"]),
        SectionSpec(title="Term", field_ids=["term"]),
        SectionSpec(title="Fees", field_ids=["fees"]),
        SectionSpec(title="Notice Address", field_ids=["noticeAddress"]),
        law_and_courts_section("Governing Law & Chosen Courts"),
        SectionSpec(title="Agreement Modifications", field_ids=["modifications"]),
    ],
)

PARTNERSHIP = DocumentSpec(
    id="partnership-agreement",
    name="Partnership Agreement",
    short_name="Agreement",
    aliases=["reseller agreement", "channel agreement", "referral agreement"],
    description=(
        "Commercial partnership in which each party performs defined "
        "obligations, addressing payment and taxes, feedback, intellectual "
        "property, confidentiality, and mutual liability terms."
    ),
    template="partnership-agreement.md",
    title="Partnership Agreement — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this "
        "Agreement as of the Effective Date."
    ),
    parties=("Company", "Partner"),
    fields=[
        effective_date(),
        text(
            "obligations",
            "Obligations",
            "What each party will do",
            ["Obligations"],
        ),
        text(
            "territory",
            "Territory",
            "Where the partnership operates",
            ["Territory"],
            long=False,
        ),
        text(
            "paymentProcess",
            "Payment process",
            "How and what each party is paid",
            ["Payment Process"],
        ),
        text(
            "paymentSchedule",
            "Payment schedule",
            "When payments fall due",
            ["Payment Schedule"],
        ),
        period("endDate", "End date", "When the partnership ends", ["End Date"]),
        text(
            "brandGuidelines",
            "Brand guidelines",
            "Rules for using each other's brand",
            ["Brand Guidelines"],
            required=False,
            empty_text="None.",
        ),
        governing_law(),
        courts("Chosen courts", ["Chosen Courts"]),
        *liability_fields(("Company", "Partner")),
        modifications("Agreement"),
    ],
    sections=[
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(title="Obligations", field_ids=["obligations"]),
        SectionSpec(title="Territory", field_ids=["territory"]),
        SectionSpec(
            title="Payment", field_ids=["paymentProcess", "paymentSchedule"]
        ),
        SectionSpec(title="End Date", field_ids=["endDate"]),
        SectionSpec(title="Brand Guidelines", field_ids=["brandGuidelines"]),
        law_and_courts_section("Governing Law & Chosen Courts"),
        *liability_sections(("Company", "Partner")),
        SectionSpec(title="Agreement Modifications", field_ids=["modifications"]),
    ],
    uncaptured=["Any Data Processing Agreement referenced by these terms"],
)

PROFESSIONAL_SERVICES = DocumentSpec(
    id="professional-services-agreement",
    name="Professional Services Agreement",
    short_name="Agreement",
    aliases=["PSA", "MSA", "master services agreement", "consulting agreement", "statement of work", "SOW", "contractor agreement"],
    description=(
        "Master services agreement for professional and consulting work "
        "delivered under statements of work, covering service performance, "
        "deliverables and IP ownership, personnel, fees and expenses, and "
        "customer policies."
    ),
    template="professional-services-agreement.md",
    title="Professional Services Agreement — Cover Page",
    attest=(
        "By signing this Cover Page, each party agrees to enter into this "
        "Agreement as of the Effective Date."
    ),
    parties=("Customer", "Provider"),
    fields=[
        effective_date(),
        # Statement of Work values, marked `sow_link` in the template.
        text(
            "deliverables",
            "Deliverables",
            "What the provider will deliver",
            ["Deliverable", "Deliverables"],
        ),
        period("sowTerm", "SOW term", "How long the statement of work runs", ["SOW Term"]),
        text(
            "fees",
            "Fees",
            "What the customer pays",
            ["Fees"],
        ),
        period(
            "paymentPeriod",
            "Payment period",
            "How long the customer has to pay an invoice",
            ["Payment Period"],
        ),
        text(
            "customerObligations",
            "Customer obligations",
            "What the customer must provide or do",
            ["Customer Obligations"],
            required=False,
            empty_text="None.",
        ),
        period(
            "rejectionPeriod",
            "Rejection period",
            "How long the customer has to reject a deliverable",
            ["Rejection Period"],
        ),
        period(
            "resubmissionPeriod",
            "Resubmission period",
            "How long the provider has to resubmit a rejected deliverable",
            ["Resubmission Period"],
        ),
        text(
            "timeOfAssignment",
            "Time of assignment",
            "When ownership of deliverables passes to the customer",
            ["Time of Assignment"],
            long=False,
            guidance='e.g. "on payment in full" or "on delivery".',
        ),
        text(
            "customerPolicies",
            "Customer policies",
            "Policies the provider must follow",
            ["Customer Policies"],
            required=False,
            empty_text="None.",
        ),
        text(
            "securityPolicy",
            "Security policy",
            "Security measures the provider must maintain",
            ["Security Policy"],
            required=False,
            empty_text="None.",
        ),
        text(
            "insuranceMinimums",
            "Insurance minimums",
            "Insurance the provider must carry",
            ["Insurance Minimums"],
            required=False,
            empty_text="None.",
        ),
        governing_law(),
        courts("Chosen courts", ["Chosen Courts"]),
        *liability_fields(("Customer", "Provider")),
        modifications("Agreement"),
    ],
    sections=[
        SectionSpec(title="Effective Date", field_ids=["effectiveDate"]),
        SectionSpec(title="Deliverables", field_ids=["deliverables"]),
        SectionSpec(title="SOW Term", field_ids=["sowTerm"]),
        SectionSpec(title="Fees", field_ids=["fees", "paymentPeriod"]),
        SectionSpec(title="Customer Obligations", field_ids=["customerObligations"]),
        SectionSpec(
            title="Acceptance",
            hint="How deliverables are accepted or rejected",
            field_ids=["rejectionPeriod", "resubmissionPeriod", "timeOfAssignment"],
        ),
        SectionSpec(
            title="Policies",
            field_ids=["customerPolicies", "securityPolicy", "insuranceMinimums"],
        ),
        law_and_courts_section("Governing Law & Chosen Courts"),
        *liability_sections(("Customer", "Provider")),
        SectionSpec(title="Agreement Modifications", field_ids=["modifications"]),
    ],
    uncaptured=["Any Data Processing Agreement referenced by these terms"],
)

#: Every document type, in the order the catalogue lists them.
SPECS: tuple[DocumentSpec, ...] = (
    AI_ADDENDUM,
    BUSINESS_ASSOCIATE,
    CLOUD_SERVICE,
    DATA_PROCESSING,
    DESIGN_PARTNER,
    MUTUAL_NDA,
    PARTNERSHIP,
    PILOT,
    PROFESSIONAL_SERVICES,
    SERVICE_LEVEL,
    SOFTWARE_LICENSE,
)
