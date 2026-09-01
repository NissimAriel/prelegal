'use client'

import { toHtml } from '@/lib/render'
import {
  formatDate,
  mndaTerm,
  termOfConfidentiality,
  UNFILLED,
  type MndaFields,
  type Party,
} from '@/lib/fields'
import type { CoverPageProse } from '@/lib/templates'

/**
 * The Mutual NDA Cover Page, rendered from the user's answers.
 *
 * Unlike the Standard Terms — immutable legal prose rendered straight from
 * templates/mutual-nda.md — the Cover Page is a fill-in form artifact:
 * templates/mutual-nda-coverpage.md is a skeleton of bracketed prompts,
 * `- [x]` checkbox pairs and an empty signature table. Its structure is
 * reproduced here so each field renders as a resolved statement of what the
 * parties agreed rather than a form still waiting to be filled.
 *
 * Its two pieces of substantive text — the preamble and the CC BY attribution —
 * come from the template itself via `extractCoverPageProse`, so no legal wording
 * is duplicated into this component.
 */

/** A value the user supplied, or a placeholder until they do. */
function Value({ children }: { children: string }) {
  return (
    <span className={children === UNFILLED ? 'unfilled' : 'filled'}>
      {children}
    </span>
  )
}

/** One labelled Cover Page section. */
function Section({
  title,
  hint,
  children,
}: {
  title: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <section className="coverSection">
      <h2>
        {title}
        {hint ? <span className="hint">{hint}</span> : null}
      </h2>
      {children}
    </section>
  )
}

/**
 * The signature block, in the order the template lays it out. `Signature` and
 * `Date` are left blank for wet signing; the rest are filled from the form.
 */
const SIGNATURE_ROWS: ReadonlyArray<{
  label: string
  hint?: string
  get?: (party: Party) => string
}> = [
  { label: 'Signature' },
  { label: 'Print Name', get: (p) => p.name },
  { label: 'Title', get: (p) => p.title },
  { label: 'Company', get: (p) => p.company },
  {
    label: 'Notice Address',
    hint: 'Email or postal address',
    get: (p) => p.noticeAddress,
  },
  { label: 'Date' },
]

export default function CoverPage({
  fields,
  prose,
}: {
  fields: MndaFields
  prose: CoverPageProse
}) {
  const parties = [fields.party1, fields.party2]

  return (
    <article className="coverPage">
      <h1>Mutual Non-Disclosure Agreement</h1>

      <div
        className="preamble"
        dangerouslySetInnerHTML={{ __html: toHtml(prose.preamble) }}
      />

      <Section title="Purpose" hint="How Confidential Information may be used">
        <p className="purpose">
          <Value>{fields.purpose.trim() || UNFILLED}</Value>
        </p>
      </Section>

      <Section title="Effective Date">
        <p>
          <Value>{formatDate(fields.effectiveDate)}</Value>
        </p>
      </Section>

      <Section title="MNDA Term" hint="The length of this MNDA">
        <p>
          <Value>{mndaTerm(fields).cover}</Value>
        </p>
      </Section>

      <Section
        title="Term of Confidentiality"
        hint="How long Confidential Information is protected"
      >
        <p>
          <Value>{termOfConfidentiality(fields).cover}</Value>
        </p>
      </Section>

      <Section title="Governing Law &amp; Jurisdiction">
        <p>
          Governing Law: <Value>{fields.governingLaw.trim() || UNFILLED}</Value>
        </p>
        <p>
          Jurisdiction: courts located in{' '}
          <Value>{fields.jurisdiction.trim() || UNFILLED}</Value>
        </p>
      </Section>

      <Section title="MNDA Modifications">
        {fields.modifications.trim() ? (
          <p className="modifications">{fields.modifications.trim()}</p>
        ) : (
          <p>None.</p>
        )}
      </Section>

      <p className="attest">
        By signing this Cover Page, each party agrees to enter into this MNDA as
        of the Effective Date.
      </p>

      <table className="signatures">
        <thead>
          <tr>
            <th scope="col" />
            <th scope="col">Party 1</th>
            <th scope="col">Party 2</th>
          </tr>
        </thead>
        <tbody>
          {SIGNATURE_ROWS.map(({ label, hint, get }) => (
            <tr key={label}>
              <th scope="row">
                {label}
                {hint ? <span className="hint">{hint}</span> : null}
              </th>
              {parties.map((party, i) => (
                <td
                  key={i}
                  className={get ? undefined : 'signatureLine'}
                >
                  {get ? <Value>{get(party) || UNFILLED}</Value> : null}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div
        className="attribution"
        dangerouslySetInnerHTML={{ __html: toHtml(prose.attribution) }}
      />
    </article>
  )
}
