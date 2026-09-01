/**
 * The shape of a Mutual NDA, as captured from the user.
 *
 * Field names mirror the section headings on the Common Paper Mutual NDA Cover
 * Page (templates/mutual-nda-coverpage.md) so the two stay easy to reconcile.
 */

/** One signatory to the agreement. */
export interface Party {
  name: string
  title: string
  company: string
  /** Either an email or a postal address, per the Cover Page's own guidance. */
  noticeAddress: string
}

export interface MndaFields {
  /** How Confidential Information may be used. */
  purpose: string
  /** ISO `yyyy-mm-dd`, as produced by `<input type="date">`. */
  effectiveDate: string
  /** Whether the MNDA expires on a fixed term or runs until terminated. */
  termType: 'expires' | 'untilTerminated'
  /** Years until expiry. Only meaningful when `termType` is `expires`. */
  termYears: number
  /** Whether confidentiality lasts a fixed term or in perpetuity. */
  confidentialityType: 'years' | 'perpetuity'
  /** Years of confidentiality. Only meaningful when `confidentialityType` is `years`. */
  confidentialityYears: number
  /** Governing law, as a US state. */
  governingLaw: string
  /** Courts with jurisdiction, e.g. "New Castle, DE". */
  jurisdiction: string
  /** Free-text list of any modifications to the standard MNDA. */
  modifications: string
  party1: Party
  party2: Party
}

const emptyParty = (): Party => ({
  name: '',
  title: '',
  company: '',
  noticeAddress: '',
})

/**
 * Starting values for a new agreement. The purpose and term defaults match the
 * suggested values printed in the Common Paper Cover Page template.
 */
export const defaultFields = (): MndaFields => ({
  purpose:
    'Evaluating whether to enter into a business relationship with the other party.',
  effectiveDate: '',
  termType: 'expires',
  termYears: 1,
  confidentialityType: 'years',
  confidentialityYears: 1,
  governingLaw: '',
  jurisdiction: '',
  modifications: '',
  party1: emptyParty(),
  party2: emptyParty(),
})

/**
 * Fields that must be filled before the agreement is complete enough to
 * download. Everything else either has a sensible default or is genuinely
 * optional (modifications, and each party's title).
 */
const REQUIRED: ReadonlyArray<{ label: string; get: (f: MndaFields) => string }> = [
  { label: 'Purpose', get: (f) => f.purpose },
  { label: 'Effective Date', get: (f) => f.effectiveDate },
  { label: 'Governing Law', get: (f) => f.governingLaw },
  { label: 'Jurisdiction', get: (f) => f.jurisdiction },
  { label: 'Party 1 print name', get: (f) => f.party1.name },
  { label: 'Party 1 company', get: (f) => f.party1.company },
  { label: 'Party 1 notice address', get: (f) => f.party1.noticeAddress },
  { label: 'Party 2 print name', get: (f) => f.party2.name },
  { label: 'Party 2 company', get: (f) => f.party2.company },
  { label: 'Party 2 notice address', get: (f) => f.party2.noticeAddress },
]

/** Human-readable labels of every required field the user has left blank. */
export function missingFields(fields: MndaFields): string[] {
  return REQUIRED.filter(({ get }) => get(fields).trim() === '').map(
    ({ label }) => label,
  )
}

/** Placeholder shown in the document wherever a value has not been entered yet. */
export const UNFILLED = '—'

/**
 * Formats an ISO date as e.g. "March 4, 2026". Returns the `UNFILLED`
 * placeholder for an empty value, and echoes anything unparseable back
 * unchanged rather than rendering "Invalid Date" into a legal document.
 */
export function formatDate(iso: string): string {
  if (!iso.trim()) return UNFILLED
  const date = new Date(`${iso}T00:00:00`)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const years = (n: number): string => `${n} ${n === 1 ? 'year' : 'years'}`

/**
 * A term of the agreement, in the two voices the document needs.
 *
 * Both are required and neither can be derived from the other, so each choice
 * states both here — that way the branch on which option the user picked lives
 * in exactly one place, and the Cover Page and the Standard Terms cannot drift
 * into describing the same term differently.
 */
export interface TermPhrasing {
  /** Cover Page voice: a complete statement of what the parties agreed. */
  cover: string
  /** Standard Terms voice: a noun phrase that slots into a sentence. */
  reference: string
}

/** The length of the MNDA. */
export function mndaTerm(fields: MndaFields): TermPhrasing {
  if (fields.termType === 'expires') {
    const span = `${years(fields.termYears)} from the Effective Date`
    return { cover: `Expires ${span}.`, reference: span }
  }
  return {
    cover: 'Continues until terminated in accordance with the terms of the MNDA.',
    reference: 'period until this MNDA is terminated in accordance with its terms',
  }
}

/** How long Confidential Information stays protected. */
export function termOfConfidentiality(fields: MndaFields): TermPhrasing {
  if (fields.confidentialityType === 'years') {
    const span =
      `${years(fields.confidentialityYears)} from the Effective Date, but in ` +
      'the case of trade secrets until the Confidential Information is no ' +
      'longer considered a trade secret under applicable laws'
    return { cover: `${span}.`, reference: span }
  }
  return { cover: 'In perpetuity.', reference: 'perpetuity' }
}
